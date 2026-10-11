"""Parallel feeds, safe public article extraction, and explicit excerpt fallbacks."""

import asyncio
import hashlib
import ipaddress
import re
import socket
from urllib.parse import urlparse

import httpx
import trafilatura
from defusedxml import ElementTree

from backend.cache import DiskCache, cache_key
from backend.config import COUNTRIES, settings
from backend.http import request
from backend.models import Article


def strip_html(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


def headline_language(headline: str, edition: str) -> str:
    language = COUNTRIES[edition]["language"]
    if language == "ja" and not re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", headline):
        return "en"
    if language == "hi" and not re.search(r"[\u0900-\u097f]", headline):
        return "en"
    return language


def parse_rss(text: str, country: str) -> list[Article]:
    root = ElementTree.fromstring(text)
    articles = []
    seen = set()
    for item in root.findall(".//item")[:20]:
        title = item.findtext("title", "").strip()
        url = item.findtext("link", "").strip()
        source = item.find("source")
        outlet = source.text if source is not None and source.text else "Unknown outlet"
        suffix = f" - {outlet}"
        title = title.removesuffix(suffix)
        if not title or not url.startswith("https://") or outlet in seen:
            continue
        seen.add(outlet)
        # Google's description often repeats a linked headline, not article text.
        articles.append(
            Article(
                id=hashlib.sha256(url.encode()).hexdigest()[:16],
                country=country,
                outlet=outlet,
                url=url,
                headline=title,
                text=title,
                language=headline_language(title, country),
                published=item.findtext("pubDate", ""),
                coverage="headline",
                retrieval="Google News RSS; edition is not outlet nationality",
            )
        )
        if len(articles) == 2:
            break
    return articles


async def public_url(url: str) -> bool:
    """Reject non-public destinations at every redirect; no localhost/file access."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or parsed.username or parsed.password:
        return False
    if not parsed.hostname or parsed.port not in (None, 80, 443):
        return False
    try:
        answers = await asyncio.to_thread(socket.getaddrinfo, parsed.hostname, None)
        return bool(answers) and all(ipaddress.ip_address(a[4][0]).is_global for a in answers)
    except (OSError, ValueError):
        return False


async def extract_article(client: httpx.AsyncClient, article: Article) -> Article:
    if "news.google.com" in str(article.url):
        return article  # opaque redirect links; don't claim full-text extraction
    url = str(article.url)
    try:
        for _ in range(4):
            if not await public_url(url):
                return article
            async with client.stream("GET", url, follow_redirects=False, timeout=7) as response:
                if response.is_redirect:
                    url = str(response.url.join(response.headers["location"]))
                    continue
                if response.status_code != 200 or "text/html" not in response.headers.get(
                    "content-type", ""
                ):
                    return article
                chunks, size = [], 0
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if size > 1_500_000:
                        return article
                    chunks.append(chunk)
            content = await asyncio.to_thread(trafilatura.extract, b"".join(chunks))
            if content and len(content) > 350:
                return article.model_copy(update={"text": content[:10000], "coverage": "full_text"})
            return article
    except (httpx.HTTPError, ValueError, OSError):
        return article
    return article


class Fetcher:
    def __init__(self, client: httpx.AsyncClient, cache: DiskCache):
        self.client, self.cache = client, cache

    async def api(self, query: str, country: str, provider: str) -> list[Article]:
        language = COUNTRIES[country]["language"]
        if provider == "gnews":
            key = settings.news_api_key if settings.news_provider == "gnews" else ""
            if not key:
                raise RuntimeError("GNews key missing")
            response = await request(
                self.client,
                "GET",
                "https://gnews.io/api/v4/search",
                params={"q": query, "country": country, "lang": language, "max": 2, "apikey": key},
            )
            rows = response.json().get("articles", [])
        else:
            key = settings.newsdata_api_key or (
                settings.news_api_key if settings.news_provider == "newsdata" else ""
            )
            if not key:
                raise RuntimeError("NewsData key missing")
            response = await request(
                self.client,
                "GET",
                "https://newsdata.io/api/1/latest",
                params={"q": query, "country": country, "language": language, "apikey": key},
            )
            rows = response.json().get("results", [])
        articles = []
        for row in rows[:2]:
            url = row.get("url") or row.get("link")
            title = strip_html(row.get("title") or "")
            if not url or not title:
                continue
            source = row.get("source") or {}
            text = strip_html(row.get("description") or title)
            articles.append(
                Article(
                    id=hashlib.sha256(url.encode()).hexdigest()[:16],
                    country=country,
                    outlet=source.get("name")
                    or row.get("source_name")
                    or row.get("source_id")
                    or "Unknown outlet",
                    url=url,
                    headline=title,
                    text=text,
                    language=language,
                    published=row.get("publishedAt") or row.get("pubDate") or "",
                    coverage="excerpt" if text != title else "headline",
                    retrieval=provider,
                )
            )
        if not articles:
            raise RuntimeError("No matching coverage in feed")
        return articles

    async def rss(self, query: str, country: str) -> list[Article]:
        language = COUNTRIES[country]["language"]
        edition = country.upper()
        response = await request(
            self.client,
            "GET",
            "https://news.google.com/rss/search",
            follow_redirects=True,
            params={
                "q": query,
                "hl": f"{language}-{edition}",
                "gl": edition,
                "ceid": f"{edition}:{language}",
            },
        )
        articles = parse_rss(response.text, country)
        if not articles:
            raise RuntimeError("No matching Google News RSS headlines")
        return articles

    async def fetch(self, query: str, country: str) -> tuple[list[Article], str]:
        key = cache_key("feed", query, country)
        cached = self.cache.get(key)
        if cached:
            return [Article.model_validate(a) for a in cached], "Using disk-cached coverage"
        messages = []
        providers = [settings.news_provider]
        if settings.news_provider == "gnews" and settings.newsdata_api_key:
            providers.append("newsdata")
        for provider in providers:
            try:
                articles = await self.api(query, country, provider)
                break
            except (httpx.HTTPError, ValueError, KeyError, RuntimeError):
                messages.append(f"{provider} unavailable")
        else:
            try:
                articles = await self.rss(query, country)
                messages.append("using Google News RSS headlines")
            except (httpx.HTTPError, ValueError, RuntimeError, ElementTree.ParseError):
                stale = self.cache.get(key, ttl=None)
                if stale:
                    return [
                        Article.model_validate(a) for a in stale
                    ], "Feeds unavailable; using older cached coverage"
                raise RuntimeError("Feeds unavailable; try a cached demo event") from None
        articles = await asyncio.gather(*(extract_article(self.client, a) for a in articles))
        self.cache.put(key, [a.model_dump(mode="json") for a in articles])
        return articles, "; ".join(messages) or "Coverage retrieved"
