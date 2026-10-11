"""Improve COP28 publisher sampling; capture a second outlet in each edition."""

import asyncio

import httpx

from backend.analysis import Analyzer
from backend.cache import DiskCache, cache_key
from backend.config import ROOT, settings
from backend.fetching import Fetcher
from backend.models import Article, CountryResult, Report

SEARCHES = {
    "us": "COP28 fossil fuels site:cnbc.com after:2023-12-12 before:2023-12-17",
    "gb": "COP28 fossil fuels after:2023-12-12 before:2023-12-17",
    "fr": "COP28 énergies fossiles after:2023-12-12 before:2023-12-17",
    "de": "COP28 fossile Brennstoffe after:2023-12-12 before:2023-12-17",
    "jp": "COP28 化石燃料 after:2023-12-12 before:2023-12-17",
    "in": "COP28 जीवाश्म ईंधन after:2023-12-12 before:2023-12-17",
}


async def main():
    cache = DiskCache()
    async with httpx.AsyncClient(timeout=15) as client:
        fetcher, analyzer = Fetcher(client, cache), Analyzer(client, cache)
        countries = []
        for country, query in SEARCHES.items():
            key = cache_key("refined-feed", query, country)
            stored = cache.get(key, ttl=None)
            articles = (
                [Article.model_validate(a) for a in stored]
                if stored
                else await fetcher.rss(query, country)
            )
            cache.put(key, [a.model_dump(mode="json") for a in articles])
            articles = list({article.outlet: article for article in articles}.values())
            outlets = []
            for article in articles:
                framing_key = cache_key(
                    "framing", article.country, article.id, article.text, settings.groq_model
                )
                needs_call = cache.get(framing_key, ttl=None) is None
                outlets.append(await analyzer.frame(article))
                print(country, article.outlet, "validated", flush=True)
                if needs_call:
                    await asyncio.sleep(12)
            countries.append(
                CountryResult(
                    country=country,
                    outlets=outlets,
                    status="ready",
                    message="Two captured RSS headlines; cached Groq analysis",
                )
            )
        old = Report.model_validate_json((ROOT / "data/demo/cop28-en.json").read_text())
        old.countries = countries
        old.notices[1] = "Up to two outlets per edition. A feed edition is not a country’s opinion."
        for language in ("en", "es", "fr"):
            await asyncio.sleep(40)
            old.language = language
            old.id = f"demo-cop28-{language}"
            old.synthesis = await analyzer.synthesize(
                [o for c in countries for o in c.outlets], language
            )
            (ROOT / f"data/demo/cop28-{language}.json").write_text(old.model_dump_json(indent=2))
            print(language, "refined report saved", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
