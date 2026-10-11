import asyncio
import json

import httpx
from pydantic import BaseModel

from backend.cache import DiskCache, cache_key
from backend.config import ROOT, settings
from backend.http import request
from backend.models import THEMES, Article, Framing, OutletAnalysis, Synthesis

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class EvidenceError(ValueError):
    pass


def validate_evidence(article: Article, framing: Framing) -> None:
    text = article.headline + "\n" + article.text
    if sorted(t.theme for t in framing.themes) != sorted(THEMES):
        raise EvidenceError("Expected each theme exactly once")
    quotes = [c.quote for c in framing.key_claims] + [t.quote for t in framing.themes if t.score]
    invalid_quotes = [quote for quote in quotes if not quote.strip() or quote not in text]
    if invalid_quotes:
        raise EvidenceError(
            f"Exact source mismatch for quote(s): {invalid_quotes!r}. Preserve accents and curly apostrophes."
        )
    translation = framing.translated_headline + "\n" + framing.translated_text
    invalid_words = [word.word for word in framing.loaded_words if word.word not in translation]
    if invalid_words:
        raise EvidenceError(
            f"Loaded word(s) missing from your English translation: {invalid_words!r}"
        )
    cap = {"headline": 0.45, "excerpt": 0.70, "full_text": 0.90}[article.coverage]
    if framing.confidence > cap:
        raise EvidenceError("Confidence exceeds evidence coverage cap")


def validate_references(synthesis: Synthesis, outlets: list[OutletAnalysis]) -> None:
    valid = {o.article.id for o in outlets}
    items = [
        *synthesis.summary,
        *synthesis.simple_summary,
        *synthesis.clusters,
        *synthesis.missing_voices,
    ]
    if not synthesis.summary:
        raise EvidenceError("Summary must contain at least one supported point")
    for item in items:
        if not set(item.source_ids).issubset(valid):
            raise EvidenceError("Synthesis cites unknown sources")
    for cluster in synthesis.clusters:
        count = len(set(cluster.source_ids))
        if cluster.status in ("shared", "disputed") and count < 2:
            raise EvidenceError("Cross-source cluster needs two sources")
        if cluster.status == "single_source" and count != 1:
            raise EvidenceError("Single-source cluster must cite one source")


class Analyzer:
    def __init__(self, client: httpx.AsyncClient, cache: DiskCache):
        self.client, self.cache = client, cache
        self.slots = asyncio.Semaphore(2)

    async def structured(self, prompt: str, data: dict, model: type[BaseModel]):
        if not settings.groq_api_key:
            raise RuntimeError("Groq key missing; select a cached demo event")
        schema = model.model_json_schema()
        article = data.get("article", {})
        if model is Framing:
            schema["properties"]["key_claims"]["maxItems"] = 3
            schema["properties"]["loaded_words"]["maxItems"] = 3
            schema["properties"]["themes"]["minItems"] = 6
            schema["properties"]["themes"]["maxItems"] = 6
        if model is Framing and article.get("coverage") == "headline":
            # Headlines are short enough to constrain quotes at generation time.
            # The validator still checks exact provenance for all coverage types.
            headline = article["headline"]
            schema["$defs"]["Claim"]["properties"]["quote"]["enum"] = [headline]
            schema["$defs"]["ThemeScore"]["properties"]["quote"]["enum"] = ["", headline]
        body = {
            "model": settings.groq_model,
            "messages": [
                {"role": "system", "content": (ROOT / f"backend/prompts/{prompt}.txt").read_text()},
                {"role": "user", "content": json.dumps(data, ensure_ascii=False)},
            ],
            "temperature": 0.1,
            "reasoning_effort": "low",
            "max_completion_tokens": 3500 if prompt == "synthesis" else 4500,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": model.__name__,
                    "strict": True,
                    "schema": schema,
                },
            },
        }
        async with self.slots:
            response = await request(
                self.client,
                "POST",
                GROQ_URL,
                json=body,
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                timeout=65,
            )
        return model.model_validate_json(response.json()["choices"][0]["message"]["content"])

    async def frame(self, article: Article) -> OutletAnalysis:
        key = cache_key("framing", article.country, article.id, article.text, settings.groq_model)
        cached = self.cache.get(key, ttl=None)
        if cached:
            framing = Framing.model_validate(cached)
            validate_evidence(article, framing)
            return OutletAnalysis(article=article, framing=framing, method="groq")
        reminder = "Use exact original quotes and coverage confidence cap."
        for attempt in range(2):
            framing = await self.structured(
                "framing",
                {
                    "article": article.model_dump(mode="json"),
                    "validation_reminder": reminder,
                },
                Framing,
            )
            try:
                validate_evidence(article, framing)
                self.cache.put(key, framing.model_dump(mode="json"))
                return OutletAnalysis(article=article, framing=framing, method="groq")
            except EvidenceError as exc:
                if attempt:
                    raise
                reminder = f"Previous output failed: {exc}. Copy case-sensitive words exactly from your own translation. Return a corrected complete object."
        raise EvidenceError("No valid framing returned")

    async def synthesize(self, outlets: list[OutletAnalysis], language: str) -> Synthesis:
        if not outlets:
            raise EvidenceError("No successfully analyzed sources")
        key = cache_key(
            "synthesis",
            language,
            settings.groq_model,
            json.dumps([o.model_dump(mode="json") for o in outlets], sort_keys=True),
        )
        cached = self.cache.get(key, ttl=None)
        if cached:
            synthesis = Synthesis.model_validate(cached)
        else:
            synthesis = await self.structured(
                "synthesis",
                {
                    "language": language,
                    "outlets": [
                        {
                            "id": o.article.id,
                            "outlet": o.article.outlet,
                            "country": o.article.country,
                            "headline": o.framing.translated_headline,
                            "coverage": o.article.coverage,
                            "claims": [c.model_dump() for c in o.framing.key_claims],
                            "themes": [
                                {"theme": t.theme, "score": t.score}
                                for t in o.framing.themes
                                if t.score
                            ],
                            "not_visible": o.framing.omitted,
                        }
                        for o in outlets
                    ],
                },
                Synthesis,
            )
        validate_references(synthesis, outlets)
        self.cache.put(key, synthesis.model_dump(mode="json"))
        return synthesis
