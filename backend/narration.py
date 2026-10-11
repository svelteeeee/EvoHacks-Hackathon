"""On-demand multi-voice speech. Cached demo playback never spends credits."""

import asyncio
import json
import os
import tempfile

import httpx
from fastapi import HTTPException

from backend.cache import DiskCache, cache_key
from backend.config import COUNTRIES, ROOT, settings
from backend.http import request
from backend.models import Report

VOICE_LOCK = asyncio.Lock()
AUDIO_LOCK = asyncio.Lock()


def transcript_for(report: Report, country: str) -> str:
    if country == "summary":
        return " ".join(point.text for point in report.synthesis.summary)
    if country not in COUNTRIES:
        raise HTTPException(404, "Unknown district")
    outlets = next((c.outlets for c in report.countries if c.country == country), [])
    if not outlets:
        raise HTTPException(404, "No coverage to narrate in this district")
    parts = [
        f"From the {COUNTRIES[country]['name']} news edition. This is a sample, not national opinion."
    ]
    for outlet in outlets:
        parts.append(f"{outlet.article.outlet}: {outlet.framing.translated_headline}.")
        parts.extend(claim.text for claim in outlet.framing.key_claims[:2])
    return " ".join(parts)


async def available_voices(client: httpx.AsyncClient) -> list[str]:
    cache = DiskCache()
    key = cache_key("elevenlabs-voices")
    async with VOICE_LOCK:
        value = cache.get(key, ttl=86400)
        if value:
            return value
        response = await request(
            client,
            "GET",
            "https://api.elevenlabs.io/v2/voices",
            params={"voice_type": "default", "page_size": 20},
            headers={"xi-api-key": settings.elevenlabs_api_key},
        )
        voices = [v["voice_id"] for v in response.json().get("voices", []) if v.get("voice_id")]
        if not voices:
            raise HTTPException(
                503, "No ElevenLabs voices available. Check your voice permissions."
            )
        cache.put(key, voices)
        return voices


def audio_key(report: Report, country: str, transcript: str) -> str:
    return cache_key("audio", report.id, country, transcript)


async def narrate(report: Report, country: str, *, generate_demo: bool = False) -> dict:
    transcript = transcript_for(report, country)
    key = audio_key(report, country, transcript)
    path = settings.audio_dir / f"{key}.mp3"
    static_path = ROOT / f"data/demo/audio/{key}.mp3"
    result = {"url": f"/api/audio/{key}", "transcript": transcript, "cached": True}
    if path.exists() or static_path.exists():
        return result
    if report.mode == "demo" and not generate_demo:
        raise HTTPException(
            503, "Narration is not cached for this demo yet. The written briefing is ready."
        )
    if not settings.elevenlabs_api_key:
        raise HTTPException(
            503, "Audio key missing. Read the written briefing or add ELEVENLABS_API_KEY."
        )
    if len(transcript) > 4500:
        raise HTTPException(422, "Briefing too long for narration. Use a shorter sample.")
    async with AUDIO_LOCK:
        if path.exists() or static_path.exists():
            return result
        try:
            async with httpx.AsyncClient(timeout=40) as client:
                voices = await available_voices(client)
                index = 0 if country == "summary" else list(COUNTRIES).index(country) + 1
                voice = voices[index % len(voices)]
                response = await request(
                    client,
                    "POST",
                    f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
                    params={"output_format": "mp3_44100_128"},
                    headers={"xi-api-key": settings.elevenlabs_api_key},
                    json={"text": transcript, "model_id": "eleven_multilingual_v2"},
                )
                if not response.headers.get("content-type", "").startswith("audio/"):
                    raise HTTPException(
                        503, "Voice provider returned no audio. Try the written briefing."
                    )
                destination = ROOT / "data/demo/audio" if generate_demo else settings.audio_dir
                destination.mkdir(parents=True, exist_ok=True)
                fd, name = tempfile.mkstemp(dir=destination, suffix=".tmp")
                with os.fdopen(fd, "wb") as file:
                    file.write(response.content)
                os.replace(name, destination / f"{key}.mp3")
                (destination / f"{key}.json").write_text(
                    json.dumps(
                        {
                            "transcript": transcript,
                            "voice_id": voice,
                            "model": "eleven_multilingual_v2",
                        }
                    )
                )
        except httpx.HTTPError:
            raise HTTPException(
                503, "Voice provider unavailable or out of credits. The written briefing is ready."
            ) from None
    return result | {"cached": False}
