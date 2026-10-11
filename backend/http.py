"""Bounded retries without logging URLs, query credentials, or response bodies."""

import asyncio
import random
import re

import httpx


async def request(client: httpx.AsyncClient, method: str, url: str, **kwargs) -> httpx.Response:
    for attempt in range(3):
        try:
            response = await client.request(method, url, **kwargs)
            if response.status_code not in (429, 500, 502, 503, 504):
                response.raise_for_status()
                return response
            if response.status_code == 429 and "tokens per day" in response.text.lower():
                response.raise_for_status()  # Daily quota: immediate stop, not repeated spend.
            if attempt == 2:
                response.raise_for_status()
            try:
                delay = min(float(response.headers.get("retry-after", "0")), 60)
            except ValueError:
                delay = 0
            if response.status_code == 429 and not delay:
                match = re.search(r"try again in ([0-9.]+)s", response.text)
                delay = min(float(match.group(1)), 60) if match else 5
        except (httpx.TimeoutException, httpx.TransportError):
            if attempt == 2:
                raise
            delay = 0
        await asyncio.sleep(max(delay, 0.5 * 2**attempt) + random.random() * 0.15)
    raise RuntimeError("Retry budget exhausted")
