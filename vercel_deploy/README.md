# News Bridge — Vercel deploy

Static, self-contained build. **No backend or API keys needed** — it renders the
night-city intro, the six-district heatmap and the three cached demo stories
(COP28, Chandrayaan-3, Paris Olympics) entirely from bundled JSON.

## Deploy (two ways)

**A. Drag & drop (fastest):** unzip this folder and drop it onto
https://vercel.com/new — Vercel deploys it as a static site.

**B. CLI / Git:** push these files to a GitHub repo, import it in Vercel,
root directory = repo root (where `vercel.json` lives). Framework preset:
**Other**. No build command, no output directory override.

## What runs here
- City intro (seeded Canvas 2D), hero, search UI, command palette (Cmd/Ctrl+K).
- Three cached events in English with the full report: summary, theme heatmap,
  numbered matrix, evidence drill-down, claim cross-check, missing voices.
- Original-headline toggle, simple-summary toggle, print/Save-as-PDF.

## What does NOT run on static hosting
Live news retrieval, Groq translation/analysis, and ElevenLabs narration need the
Python FastAPI backend (`uv run uvicorn backend.app:app`) and are disabled here —
the app detects no backend and serves the cached pack instead. "Live search" will
show an offline notice.

Files: `index.html`, `assets/` (JS/CSS/fonts), `config.json`, `demo/*.json`.
