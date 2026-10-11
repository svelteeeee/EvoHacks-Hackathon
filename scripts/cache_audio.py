"""Generate demo speech once; ordinary demo playback never calls ElevenLabs."""

import asyncio

from fastapi import HTTPException

from backend.config import ROOT
from backend.models import Report
from backend.narration import narrate


async def main():
    for path in sorted((ROOT / "data/demo").glob("*-en.json")):
        report = Report.model_validate_json(path.read_text())
        for country in ("summary", "us", "gb", "fr", "de", "jp", "in"):
            try:
                result = await narrate(report, country, generate_demo=True)
                print(
                    report.query,
                    country,
                    "cached audio" if result["cached"] else "generated audio",
                    flush=True,
                )
            except HTTPException as exc:
                print("Audio unavailable:", exc.detail, flush=True)
                raise RuntimeError(
                    "Audio preparation incomplete; see provider limitation above"
                ) from None


if __name__ == "__main__":
    asyncio.run(main())
