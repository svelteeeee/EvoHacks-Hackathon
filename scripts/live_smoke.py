"""Exercise the real live API with one edition; never prints provider credentials."""

import json

import httpx

from backend.config import ROOT


def main():
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=245) as client:
        response = client.post(
            "/api/analyze/stream", json={"query": "climate", "countries": ["us"], "demo": False}
        )
        events = [
            json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")
        ]
        for event in events:
            if event["stage"] != "complete":
                print(event.get("country"), event["stage"], event.get("message", ""))
        if not events or events[-1]["stage"] != "complete":
            raise RuntimeError("Live smoke test did not complete; no success claimed")
        report = events[-1]["report"]
        assert report["mode"] in ["live", "cache"]
        assert report["countries"][0]["outlets"]
        (ROOT / "docs/live-verification.json").write_text(
            json.dumps(
                {
                    "mode": report["mode"],
                    "country_count": len(report["countries"]),
                    "source_count": sum(len(c["outlets"]) for c in report["countries"]),
                    "stages": [e["stage"] for e in events],
                    "created_at": report["created_at"],
                    "browser_review": "pending",
                },
                indent=2,
            )
        )
        print("Real live API smoke passed:", report["mode"])


if __name__ == "__main__":
    main()
