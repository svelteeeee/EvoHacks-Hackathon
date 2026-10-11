"""Run the first vertical slice: three countries, validated JSON printed."""

import asyncio
import json

from backend.models import AnalysisRequest
from backend.pipeline import run_pipeline


async def main():
    report = await run_pipeline(
        AnalysisRequest(query="COP28", countries=["us", "gb", "fr"], demo=True),
        lambda _: asyncio.sleep(0),
    )
    print(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
