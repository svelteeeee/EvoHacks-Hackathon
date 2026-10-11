# Acceptance ledger

## Files and interfaces
- `backend/app.py`: async FastAPI API; `POST /api/analyze`, `POST /api/analyze/stream` (SSE over fetch), `GET /api/reports/{id}`.
- Pydantic strict models in `backend/models.py`; source quote/reference validation in `backend/analysis.py`.
- Original prompts: `backend/prompts/framing.txt`, `backend/prompts/synthesis.txt`.
- `data/demo/{cop28,moon,olympics}-{en,es,fr}.json`: captured real headlines + Groq output. `index.json` lists available events/languages. Audio under `data/demo/audio/`.
- `frontend/src/city.ts`: original seeded Canvas 2D art, cached static raster, 5.5-second first-visit intro, skipped through any click/key, guarded session storage, reduced motion, hidden-tab pause.
- `frontend/src/main.ts`: search, SSE progress, theme selection, numeric accessible matrix, source evidence dialog, original headline toggle, source filter, claim clusters, missing voices, narration, simple briefing, permalinks, print/PDF via browser.
- Secrets only in ignored `.env`. `.env.example` contains placeholders. No browser keys.
- `docs/DEMO.md`: 2:30 feature AND code walkthrough. `docs/DEVPOST.md`: judging-aligned draft.

## Implemented constraints
Six parallel country edition workers, max two sources each, 32-second feed budget and 240-second overall live pipeline budget. Two concurrent report jobs, two concurrent Groq calls per report. Retries for 429/5xx/transport errors (three attempts); bounded Retry-After. Atomic SHA-256 JSON disk caches for feed/query/country, per-source analysis, language synthesis, report ID, voices, and audio. Feed fallback chain depends on available keys: GNews → optional NewsData → RSS; a NewsData key uses NewsData → RSS directly. Missing Groq/news key uses cached demos; missing audio key permits cached playback.

## Deliberate cuts / honest limits
- No persona stereotypes or historical time-lapse.
- No ambient sound, fake waveform, or estimated karaoke timestamps. Native accessible audio player + exact transcript instead.
- Translation cards are English; neutral/simple synthesis supports six languages live, three languages cached.
- Country editions are not guaranteed national outlets. Captured headline confidence <=45%; uncalibrated AI estimates, not statistical intervals.
- Nonzero emphasis scores require exact quotes; correct quote presence does NOT prove the AI interpretation.
- No automatic clustering deduplication of syndication yet; common claims are not independent verification.
- Print report supports browser Save as PDF, not a server-generated PDF or image exporter.
- No real-browser automation is available in this environment. DOM/HTTP checks do not verify pixels, screen readers, audible playback, or laptop 60fps. Those are user checks before submission.
- Private dev preview is not public hosting. Python/trafilatura cannot be deployed as a Cloudflare Worker unchanged.
- Public GitHub push/visibility and actual video recording need final user action/authorization.
- Existing exposed credentials must be rotated before public use.

## Final observed blockers
Groq daily token quota blocked a completed final full-text live run. Schema generation now bounds claims/loaded words/themes and requests a concise translated passage with a larger completion budget; rerun needed after reset. ElevenLabs quota exhausted for further useful generation: four current English COP28 tracks and all seven English Moon/Olympics tracks are cached. No Spanish/French audio is cached. Nine demo JSON combinations pass real HTTP/SSE and provenance checks.
