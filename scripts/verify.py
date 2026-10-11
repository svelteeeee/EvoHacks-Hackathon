"""HTTP acceptance checks against the user-facing frontend proxy."""

import json
import statistics
import time

import httpx

from backend.config import ROOT
from backend.models import Report

HOST = "pv-1338ed4d0691-e1750881-d250-4c4f-b5e2-ca190bc4dd73.style.dev"


def main():
    timings = []
    with httpx.Client(
        base_url="http://127.0.0.1:3000", headers={"Host": HOST}, timeout=20
    ) as client:
        response = client.get("/")
        assert response.status_code == 200 and "text/html" in response.headers["content-type"]
        config = client.get("/api/config").json()
        for demo in config["demos"]:
            for language in demo["languages"]:
                start = time.perf_counter()
                response = client.post(
                    "/api/analyze/stream",
                    json={"query": demo["query"], "language": language, "demo": True},
                )
                events = [
                    json.loads(line[6:])
                    for line in response.text.splitlines()
                    if line.startswith("data: ")
                ]
                assert events[-1]["stage"] == "complete", events[-1]
                report = Report.model_validate(events[-1]["report"])
                assert report.mode == "demo" and len(report.countries) == 6
                assert all(c.outlets for c in report.countries)
                assert client.get(f"/api/reports/{report.id}").status_code == 200
                timings.append(round((time.perf_counter() - start) * 1000, 2))
                print(
                    demo["id"],
                    language,
                    len([o for c in report.countries for o in c.outlets]),
                    "sources",
                    timings[-1],
                    "ms",
                )
        response = client.post(
            "/api/analyze", json={"query": "unavailable cached event", "demo": True}
        )
        assert response.status_code == 422
    result = {
        "demo_http_timings_ms": timings,
        "median_ms": statistics.median(timings),
        "real_browser_checks": "pending",
        "canvas_60fps_midrange_laptop": "not_measured",
    }
    (ROOT / "docs/http-verification.json").write_text(json.dumps(result, indent=2))
    print("HTTP acceptance checks passed; browser/performance checks remain pending.")


if __name__ == "__main__":
    main()
