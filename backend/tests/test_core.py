import asyncio

import httpx
import pytest
from defusedxml.common import EntitiesForbidden
from pydantic import ValidationError

from backend.analysis import EvidenceError, validate_evidence, validate_references
from backend.cache import DiskCache, cache_key
from backend.demo import load_demo
from backend.fetching import parse_rss, public_url
from backend.http import request
from backend.models import AnalysisRequest
from backend.pipeline import run_pipeline


def outlet():
    return load_demo(AnalysisRequest(query="COP28", demo=True)).countries[0].outlets[0]


def test_cache_atomic_and_normalization(tmp_path):
    cache = DiskCache(tmp_path)
    key = cache_key(" COP28 ", "US")
    assert key == cache_key("cop28", "us")
    assert key != cache_key("cop28", "fr")
    cache.put(key, {"ok": True})
    assert cache.get(key) == {"ok": True}
    (tmp_path / f"{key}.json").write_text("broken")
    assert cache.get(key) is None
    assert not list(tmp_path.glob("*.tmp"))


def test_rss_parser_keeps_original_headline_and_source():
    text = "<rss><channel><item><title>Une nouvelle étape - France 24</title><link>https://example.org/story</link><source>France 24</source><description>Do not treat this as full text</description></item></channel></rss>"
    item = parse_rss(text, "fr")[0]
    assert item.headline == "Une nouvelle étape"
    assert item.outlet == "France 24"
    assert item.coverage == "headline"
    assert item.text == item.headline


def test_rss_rejects_entities():
    with pytest.raises(EntitiesForbidden):
        parse_rss('<!DOCTYPE rss [<!ENTITY x SYSTEM "file:///etc/passwd">]><rss>&x;</rss>', "us")


def test_evidence_rejects_invented_quote():
    item = outlet()
    item.framing.key_claims[0].quote = "A quotation that never appeared"
    with pytest.raises(EvidenceError):
        validate_evidence(item.article, item.framing)


def test_confidence_capped_for_headlines():
    item = outlet()
    item.framing.confidence = 0.9
    with pytest.raises(EvidenceError):
        validate_evidence(item.article, item.framing)


def test_summary_rejects_unknown_source():
    report = load_demo(AnalysisRequest(query="COP28", demo=True))
    report.synthesis.summary[0].source_ids = ["invented"]
    with pytest.raises(EvidenceError):
        validate_references(report.synthesis, [o for c in report.countries for o in c.outlets])


def test_request_rejects_unsupported_country_language_extra():
    for kwargs in (
        {"countries": ["xx"]},
        {"countries": ["us", "us"]},
        {"language": "xx"},
        {"secret": "x"},
    ):
        with pytest.raises(ValidationError):
            AnalysisRequest(query="COP28", **kwargs)


async def test_demo_pipeline_three_countries_no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("Demo must never call network")

    monkeypatch.setattr(httpx.AsyncClient, "request", forbidden)
    events = []

    async def emit(event):
        events.append(event)

    result = await run_pipeline(
        AnalysisRequest(query="COP28", countries=["us", "gb", "fr"], demo=True), emit
    )
    assert len(result.countries) == 3
    assert result.mode == "demo"
    assert len(events) == 3
    assert result.synthesis.summary


async def test_retries_rate_limit(monkeypatch):
    attempts = []

    async def sleep(_):
        pass

    monkeypatch.setattr(asyncio, "sleep", sleep)

    def handler(req):
        attempts.append(req)
        return httpx.Response(429 if len(attempts) < 3 else 200, headers={"retry-after": "1"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await request(client, "GET", "https://example.org")
    assert result.status_code == 200
    assert len(attempts) == 3


async def test_extraction_blocks_private_destinations():
    assert not await public_url("http://127.0.0.1/private")
    assert not await public_url("file:///etc/passwd")
    assert not await public_url("http://user:password@example.org")


async def test_api_failure_falls_back_to_rss(tmp_path, monkeypatch):
    from backend.fetching import Fetcher
    from backend.models import Article

    fake = outlet().article
    async with httpx.AsyncClient() as client:
        fetcher = Fetcher(client, DiskCache(tmp_path))

        async def dead_api(*args):
            raise RuntimeError("Rate limit")

        async def rss(*args):
            return [fake]

        async def extract(_client, article):
            return article

        monkeypatch.setattr(fetcher, "api", dead_api)
        monkeypatch.setattr(fetcher, "rss", rss)
        monkeypatch.setattr("backend.fetching.extract_article", extract)
        articles, message = await fetcher.fetch("COP28", "us")
        assert Article.model_validate(articles[0]).id == fake.id
        assert "Google News RSS" in message
        cached, message = await fetcher.fetch("COP28", "us")
        assert cached[0].id == fake.id
        assert "cached" in message


async def test_live_pipeline_parallel_failure_does_not_erase_other_countries(tmp_path, monkeypatch):
    from backend.config import settings
    from backend.models import Synthesis
    from backend.pipeline import Analyzer, Fetcher

    monkeypatch.setattr(settings, "groq_api_key", "test-not-a-real-key")
    monkeypatch.setattr(settings, "news_api_key", "test-not-a-real-key")
    monkeypatch.setattr(settings, "cache_dir", tmp_path)
    source = outlet()
    started = set()
    all_started = asyncio.Event()

    async def fetch(_self, query, country):
        started.add(country)
        if len(started) == 3:
            all_started.set()
        await asyncio.wait_for(all_started.wait(), 1)
        if country == "fr":
            raise RuntimeError("Feed timed out")
        return [
            source.article.model_copy(update={"country": country, "id": country})
        ], "Coverage retrieved"

    async def frame(_self, article):
        return source.model_copy(update={"article": article})

    async def synthesize(_self, analyses, language):
        assert len(analyses) == 2
        return Synthesis(
            summary=[{"text": "A supported shared claim", "source_ids": ["us", "gb"]}],
            simple_summary=[],
            clusters=[],
            missing_voices=[],
            caveat="Small sample",
        )

    monkeypatch.setattr(Fetcher, "fetch", fetch)
    monkeypatch.setattr(Analyzer, "frame", frame)
    monkeypatch.setattr(Analyzer, "synthesize", synthesize)
    events = []

    async def emit(event):
        events.append(event)

    result = await run_pipeline(
        AnalysisRequest(query="parallel test", countries=["us", "gb", "fr"]), emit
    )
    assert result.mode == "live"
    assert [c.status for c in result.countries] == ["ready", "ready", "failed"]
    assert any(e["stage"] == "failed" and e["country"] == "fr" for e in events)
    assert any(e["stage"] == "summarizing" for e in events)


async def test_paywall_preserves_excerpt_instead_of_empty_full_text(monkeypatch):
    from backend.fetching import extract_article

    item = outlet().article.model_copy(
        update={"url": "https://example.org/paywall", "coverage": "excerpt"}
    )

    async def safe(_url):
        return True

    monkeypatch.setattr("backend.fetching.public_url", safe)
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda req: httpx.Response(403))
    ) as client:
        result = await extract_article(client, item)
    assert result.text == item.text
    assert result.coverage == "excerpt"


async def test_failed_source_analysis_does_not_cache_invented_evidence(tmp_path, monkeypatch):
    from backend.analysis import Analyzer
    from backend.models import Framing

    item = outlet()
    calls = []
    async with httpx.AsyncClient() as client:
        analyzer = Analyzer(client, DiskCache(tmp_path))

        async def invalid(prompt, data, model):
            calls.append(data["validation_reminder"])
            framing = Framing.model_validate(item.framing.model_dump())
            framing.key_claims[0].quote = "Invented sentence"
            return framing

        monkeypatch.setattr(analyzer, "structured", invalid)
        with pytest.raises(EvidenceError):
            await analyzer.frame(item.article)
    assert len(calls) == 2
    assert "Previous output failed" in calls[1]
    assert not list(tmp_path.glob("*.json"))


def test_all_committed_demo_artifacts_have_real_evidence_and_valid_references():
    from backend.demo import list_demos

    for demo in list_demos():
        for language in demo["languages"]:
            report = load_demo(AnalysisRequest(query=demo["query"], language=language, demo=True))
            assert len(report.countries) == 6
            assert all(c.outlets for c in report.countries)
            assert report.language == language
            assert all(o.method == "groq" for c in report.countries for o in c.outlets)


def test_feed_edition_does_not_mislabel_latin_headline_as_japanese():
    from backend.fetching import headline_language

    assert headline_language("Climate justice sidelined", "jp") == "en"
    assert headline_language("COP28合意、化石燃料からの脱却", "jp") == "ja"
    assert headline_language("भारत की सफलता", "in") == "hi"


async def test_headline_quotes_constrained_in_strict_generation_schema(tmp_path, monkeypatch):
    from backend.analysis import Analyzer
    from backend.config import settings
    from backend.models import Framing

    item = outlet()
    captured = []

    def handler(req):
        import json

        captured.append(json.loads(req.content))
        return httpx.Response(
            200, json={"choices": [{"message": {"content": item.framing.model_dump_json()}}]}
        )

    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await Analyzer(client, DiskCache(tmp_path)).structured(
            "framing", {"article": item.article.model_dump(mode="json")}, Framing
        )
    schema = captured[0]["response_format"]["json_schema"]["schema"]
    assert schema["$defs"]["Claim"]["properties"]["quote"]["enum"] == [item.article.headline]
    assert schema["$defs"]["ThemeScore"]["properties"]["quote"]["enum"] == [
        "",
        item.article.headline,
    ]
    assert captured[0]["response_format"]["json_schema"]["strict"] is True


def test_rss_samples_different_outlets_not_two_same_publisher_headlines():
    text = (
        "<rss><channel>"
        + "".join(
            f"<item><title>News {i} - {source}</title><link>https://example.org/{i}</link><source>{source}</source></item>"
            for i, source in enumerate(["Publisher A", "Publisher A", "Publisher B"])
        )
        + "</channel></rss>"
    )
    assert [a.outlet for a in parse_rss(text, "us")] == ["Publisher A", "Publisher B"]
