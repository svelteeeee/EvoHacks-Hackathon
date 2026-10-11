"""Capture authentic RSS headlines and AI outputs during the event, never invent sources."""

import asyncio
import json
from datetime import UTC, datetime

import httpx

from backend.analysis import Analyzer
from backend.cache import DiskCache, cache_key
from backend.config import COUNTRIES, ROOT
from backend.fetching import Fetcher
from backend.models import Article, CountryResult, Report

EVENTS = [
    {
        "id": "cop28",
        "query": "COP28",
        "title": "The fossil fuel turning point",
        "date": "13 Dec 2023",
        "search": "COP28 fossil fuels after:2023-12-12 before:2023-12-17",
        "tag": "CLIMATE & DIPLOMACY",
    },
    {
        "id": "moon",
        "query": "Chandrayaan-3",
        "title": "One Moon. Many meanings.",
        "date": "23 Aug 2023",
        "search": "Chandrayaan-3 landing after:2023-08-22 before:2023-08-26",
        "tag": "SCIENCE & IDENTITY",
    },
    {
        "id": "olympics",
        "query": "Paris Olympics",
        "title": "A city opens to the world",
        "date": "26 Jul 2024",
        "search": "Paris Olympics opening ceremony after:2024-07-26 before:2024-07-29",
        "tag": "CULTURE & HUMAN COST",
    },
]


async def main():
    async with httpx.AsyncClient(timeout=15) as client:
        analyzer = Analyzer(client, DiskCache())
        fetcher = Fetcher(client, DiskCache())
        for event in EVENTS:
            if all(
                (ROOT / f"data/demo/{event['id']}-{language}.json").exists()
                for language in ("en", "es", "fr")
            ):
                print(event["id"], "already captured in all languages", flush=True)
                continue
            countries = []
            for country in COUNTRIES:
                feed_key = cache_key("prefetch", event["id"], country)
                cached_feed = fetcher.cache.get(feed_key, ttl=None)
                if cached_feed:
                    articles = [Article.model_validate(a) for a in cached_feed]
                else:
                    articles = await fetcher.rss(event["search"], country)
                    fetcher.cache.put(feed_key, [a.model_dump(mode="json") for a in articles])
                # One outlet per country keeps free-tier usage bounded; clearly label sample size.
                article = articles[0]
                try:
                    analysis = await analyzer.frame(article)
                except httpx.HTTPStatusError as exc:
                    code = exc.response.json().get("error", {}).get("code")
                    print("Framing provider error:", exc.response.status_code, code, flush=True)
                    raise RuntimeError("Framing request failed") from None
                await asyncio.sleep(10)
                countries.append(
                    CountryResult(
                        country=country,
                        outlets=[analysis],
                        status="ready",
                        message="Pre-fetched Google News edition headline; AI analysis cached",
                    )
                )
                print(event["id"], country, "captured and evidence-validated", flush=True)
            outlets = [o for c in countries for o in c.outlets]
            for language in ("en", "es", "fr"):
                output = ROOT / f"data/demo/{event['id']}-{language}.json"
                if output.exists():
                    continue
                await asyncio.sleep(35)
                try:
                    synthesis = await analyzer.synthesize(outlets, language)
                except httpx.HTTPStatusError as exc:
                    error = exc.response.json().get("error", {})
                    print(
                        "Synthesis provider status:",
                        exc.response.status_code,
                        error.get("code"),
                        str(error.get("message", ""))[:700],
                        flush=True,
                    )
                    raise RuntimeError("Synthesis request failed") from None
                report = Report(
                    id=f"demo-{event['id']}-{language}",
                    query=event["query"],
                    language=language,
                    mode="demo",
                    created_at=datetime.now(UTC).isoformat(),
                    countries=countries,
                    synthesis=synthesis,
                    notices=[
                        "Cached demo: real RSS headlines with pre-generated Groq analysis. No live calls.",
                        "One outlet per edition. A feed edition is not a country’s opinion.",
                        "Headline-only evidence: confidence capped at 45%. Omission means not visible here, not deliberately hidden.",
                    ],
                )
                (ROOT / f"data/demo/{event['id']}-{language}.json").write_text(
                    report.model_dump_json(indent=2)
                )
                print(event["id"], language, "summary cached", flush=True)
    (ROOT / "data/demo/index.json").write_text(
        json.dumps(
            [
                {k: v for k, v in e.items() if k != "search"} | {"languages": ["en", "es", "fr"]}
                for e in EVENTS
            ],
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
