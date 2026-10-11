import json

from backend.analysis import validate_evidence, validate_references
from backend.cache import cache_key
from backend.config import ROOT
from backend.models import AnalysisRequest, Report


def list_demos() -> list[dict]:
    return json.loads((ROOT / "data/demo/index.json").read_text())


def load_demo(request: AnalysisRequest) -> Report:
    match = next(
        (
            d
            for d in list_demos()
            if request.query.lower() in (d["id"].lower(), d["query"].lower(), d["title"].lower())
        ),
        None,
    )
    if not match:
        raise ValueError("No cached event matches. Choose one of the three demo stories.")
    path = ROOT / f"data/demo/{match['id']}-{request.language}.json"
    if not path.exists():
        raise ValueError(
            "That language is not cached for this event. Choose English or another demo language."
        )
    report = Report.model_validate_json(path.read_text())
    if set(request.countries) != {c.country for c in report.countries}:
        report.id += "-" + cache_key(",".join(sorted(request.countries)))[:8]
    report.countries = [c for c in report.countries if c.country in request.countries]
    ids = {o.article.id for c in report.countries for o in c.outlets}
    for name in ("summary", "simple_summary", "clusters", "missing_voices"):
        items = getattr(report.synthesis, name)
        retained = []
        for item in items:
            item.source_ids = [i for i in item.source_ids if i in ids]
            if not item.source_ids:
                continue
            if name == "clusters" and len(item.source_ids) == 1:
                item.status = "single_source"
            retained.append(item)
        setattr(report.synthesis, name, retained)
    outlets = [o for c in report.countries for o in c.outlets]
    for outlet in outlets:
        validate_evidence(outlet.article, outlet.framing)
    validate_references(report.synthesis, outlets)
    return report
