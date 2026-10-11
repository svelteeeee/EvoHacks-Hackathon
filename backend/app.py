import asyncio
import json
import logging
import re
from contextlib import suppress

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from backend.cache import DiskCache, cache_key
from backend.config import COUNTRIES, LANGUAGES, ROOT, settings
from backend.demo import list_demos
from backend.models import AnalysisRequest, Report
from backend.pipeline import run_pipeline

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
# HTTP client logs contain credential-bearing news URLs. Never enable them.
logging.getLogger("httpx").setLevel(logging.WARNING)
app = FastAPI(title="News Bridge", version="0.1.0")
slots = asyncio.Semaphore(2)


@app.get("/api/config")
def config():
    return {
        "countries": COUNTRIES,
        "languages": LANGUAGES,
        "demos": list_demos(),
        "keys": {
            "groq": bool(settings.groq_api_key),
            "news": bool(settings.news_api_key),
            "audio": bool(settings.elevenlabs_api_key),
        },
        "default_mode": "demo",
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze")
async def analyze(req: AnalysisRequest):
    async with slots:
        try:
            return await run_pipeline(req, lambda _: asyncio.sleep(0))
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from None
        except (RuntimeError, httpx.HTTPError, TimeoutError):
            raise HTTPException(
                503, "Live analysis unavailable. Choose a cached demo event."
            ) from None


@app.post("/api/analyze/stream")
async def stream(req: AnalysisRequest):
    async def events():
        queue = asyncio.Queue()

        async def work():
            async with slots:
                try:
                    report = await run_pipeline(req, queue.put)
                    await queue.put({"stage": "complete", "report": report.model_dump(mode="json")})
                except ValueError as exc:
                    await queue.put({"stage": "error", "message": str(exc)})
                except (RuntimeError, httpx.HTTPError, TimeoutError, KeyError, OSError) as exc:
                    logging.getLogger(__name__).warning("Analysis failed (%s)", type(exc).__name__)
                    await queue.put(
                        {
                            "stage": "error",
                            "message": "Live analysis unavailable. Try a cached demo.",
                        }
                    )
            await queue.put(None)

        task = asyncio.create_task(work())
        try:
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=15)
                except TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                if item is None:
                    break
                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


@app.get("/api/reports/{report_id}")
def report(report_id: str):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", report_id):
        raise HTTPException(404, "Report not found")
    value = DiskCache().get(cache_key("report-id", report_id), ttl=None)
    if not value:
        raise HTTPException(404, "Report not in this server's cache. Search again.")
    return Report.model_validate(value)


@app.post("/api/reports/{report_id}/audio/{country}")
async def audio(report_id: str, country: str):
    from backend.narration import narrate

    return await narrate(report(report_id), country)


@app.get("/api/audio/{audio_id}")
def audio_file(audio_id: str):
    if not re.fullmatch(r"[a-f0-9]{64}", audio_id):
        raise HTTPException(404, "Audio not found")
    path = settings.audio_dir / f"{audio_id}.mp3"
    if not path.exists():
        path = ROOT / f"data/demo/audio/{audio_id}.mp3"
    if not path.exists():
        raise HTTPException(404, "Audio not cached")
    return FileResponse(path, media_type="audio/mpeg")


if (ROOT / "frontend/dist").exists():
    app.mount("/", StaticFiles(directory=ROOT / "frontend/dist", html=True), name="frontend")
