import json

import httpx
import pytest

from backend.app import app
from backend.config import settings


@pytest.fixture
async def client():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


async def test_config_never_returns_keys(client):
    response = await client.get("/api/config")
    assert response.status_code == 200
    for secret in (settings.groq_api_key, settings.news_api_key, settings.elevenlabs_api_key):
        if secret:
            assert secret not in response.text
    assert len(response.json()["countries"]) == 6


async def test_demo_sse_and_permalink(client):
    response = await client.post("/api/analyze/stream", json={"query": "COP28", "demo": True})
    assert response.headers["content-type"].startswith("text/event-stream")
    events = [
        json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")
    ]
    assert events[-1]["stage"] == "complete"
    report = events[-1]["report"]
    assert len(report["countries"]) == 6
    stored = await client.get(f"/api/reports/{report['id']}")
    assert stored.status_code == 200
    assert stored.json()["id"] == report["id"]


async def test_missing_keys_automatically_use_demo(client, monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setattr(settings, "news_api_key", "")
    response = await client.post("/api/analyze", json={"query": "COP28"})
    assert response.status_code == 200
    assert response.json()["mode"] == "demo"


async def test_uncached_query_is_honest_error(client):
    response = await client.post(
        "/api/analyze", json={"query": "Not a captured event", "demo": True}
    )
    assert response.status_code == 422
    assert "No cached event" in response.json()["detail"]


async def test_invalid_request_and_audio_path(client):
    response = await client.post("/api/analyze", json={"query": "x", "countries": ["xx"]})
    assert response.status_code == 422
    response = await client.get("/api/audio/not-a-hash")
    assert response.status_code == 404


async def test_cached_demo_audio_without_keys(client, monkeypatch):
    monkeypatch.setattr(settings, "elevenlabs_api_key", "")
    report = (await client.post("/api/analyze", json={"query": "COP28", "demo": True})).json()
    response = await client.post(f"/api/reports/{report['id']}/audio/summary")
    assert response.status_code == 200
    assert response.json()["cached"] is True
    mp3 = await client.get(response.json()["url"])
    assert mp3.status_code == 200
    assert mp3.headers["content-type"] == "audio/mpeg"
    assert len(mp3.content) > 1000


async def test_country_subset_has_distinct_permalink_and_does_not_overwrite_full_report(client):
    full = (await client.post("/api/analyze", json={"query": "COP28", "demo": True})).json()
    subset = (
        await client.post(
            "/api/analyze", json={"query": "COP28", "demo": True, "countries": ["us", "gb", "fr"]}
        )
    ).json()
    assert full["id"] != subset["id"]
    assert len((await client.get(f"/api/reports/{full['id']}")).json()["countries"]) == 6
    assert len((await client.get(f"/api/reports/{subset['id']}")).json()["countries"]) == 3


async def test_whitespace_query_rejected_before_pipeline(client):
    response = await client.post("/api/analyze", json={"query": "   ", "demo": True})
    assert response.status_code == 422
