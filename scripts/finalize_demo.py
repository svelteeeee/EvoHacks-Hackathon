"""Sequential event refinement + speech preparation; exits on real errors."""

import asyncio
import json
from datetime import UTC, datetime

from backend.config import ROOT
from backend.models import Report
from scripts import cache_audio, refine_demo


async def main():
    await refine_demo.main()
    await cache_audio.main()
    manifest = []
    for path in sorted((ROOT / "data/demo").glob("*-*.json")):
        report = Report.model_validate_json(path.read_text())
        manifest.append(
            {
                "file": path.name,
                "captured_at": report.created_at,
                "sources": [
                    {
                        "id": o.article.id,
                        "edition": c.country,
                        "outlet": o.article.outlet,
                        "url": str(o.article.url),
                        "coverage": o.article.coverage,
                        "method": o.method,
                    }
                    for c in report.countries
                    for o in c.outlets
                ],
            }
        )
    (ROOT / "docs/demo-provenance.json").write_text(
        json.dumps(
            {"generated_at": datetime.now(UTC).isoformat(), "events": manifest},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
