import asyncio
import logging
from datetime import UTC, datetime
from uuid import uuid4

import httpx

from backend.analysis import Analyzer
from backend.cache import DiskCache, cache_key
from backend.config import COUNTRIES, settings
from backend.demo import load_demo
from backend.fetching import Fetcher
from backend.models import AnalysisRequest, CountryResult, Report

logger = logging.getLogger(__name__)


async def run_pipeline(req: AnalysisRequest, emit) -> Report:
    cache = DiskCache()
    key = cache_key("report", req.query, req.language, ",".join(req.countries))
    if req.demo or not settings.groq_api_key or not settings.news_api_key:
        report = load_demo(req)
        for country in report.countries:
            await emit(
                {
                    "country": country.country,
                    "stage": "ready",
                    "message": "Cached demo; no live requests",
                }
            )
        cache.put(cache_key("report-id", report.id), report.model_dump(mode="json"))
        return report
    cached = cache.get(key)
    if cached:
        report = Report.model_validate(cached)
        report.mode = "cache"
        for country in report.countries:
            await emit(
                {"country": country.country, "stage": "ready", "message": "Using cached analysis"}
            )
        return report
    async with httpx.AsyncClient(
        timeout=10, headers={"User-Agent": "NewsBridge/0.1 (media literacy prototype)"}
    ) as client:
        fetcher, analyzer = Fetcher(client, cache), Analyzer(client, cache)

        async def country_pipeline(country: str) -> CountryResult:
            await emit({"country": country, "stage": "fetching", "message": "Finding coverage"})
            try:
                async with asyncio.timeout(32):
                    articles, message = await fetcher.fetch(req.query, country)
                await emit({"country": country, "stage": "translating", "message": message})
                await emit(
                    {
                        "country": country,
                        "stage": "analyzing",
                        "message": "Translating and validating evidence",
                    }
                )
                outcomes = await asyncio.gather(
                    *(analyzer.frame(a) for a in articles), return_exceptions=True
                )
                outlets = [o for o in outcomes if not isinstance(o, BaseException)]
                failed = len(outcomes) - len(outlets)
                if not outlets:
                    raise RuntimeError("Analysis unavailable; try a cached demo")
                if failed:
                    message += f"; {failed} source(s) could not be validated"
                await emit({"country": country, "stage": "ready", "message": message})
                return CountryResult(
                    country=country,
                    outlets=outlets,
                    status="partial" if failed else "ready",
                    message=message,
                )
            except (
                TimeoutError,
                RuntimeError,
                ValueError,
                httpx.HTTPError,
                OSError,
                KeyError,
            ) as exc:
                logger.warning("Country pipeline failed: %s (%s)", country, type(exc).__name__)
                message = f"{COUNTRIES[country]['name']} unavailable. Try a cached demo."
                await emit({"country": country, "stage": "failed", "message": message})
                return CountryResult(country=country, outlets=[], status="failed", message=message)

        async with asyncio.timeout(240):
            countries = await asyncio.gather(*(country_pipeline(c) for c in req.countries))
            await emit(
                {
                    "country": None,
                    "stage": "summarizing",
                    "message": "Comparing claims and finding common ground",
                }
            )
            synthesis = await analyzer.synthesize(
                [o for c in countries for o in c.outlets], req.language
            )
    report = Report(
        id=uuid4().hex,
        query=req.query,
        language=req.language,
        mode="live",
        created_at=datetime.now(UTC).isoformat(),
        countries=countries,
        synthesis=synthesis,
        notices=[
            "AI analysis of retrieved text, not ground truth or national public opinion.",
            "Country filters describe feed editions; outlet nationality may differ.",
        ],
    )
    cache.put(key, report.model_dump(mode="json"))
    cache.put(cache_key("report-id", report.id), report.model_dump(mode="json"))
    return report
