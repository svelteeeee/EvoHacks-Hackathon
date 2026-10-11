# Provenance and dependencies

All app code, prompts, procedural building/bridge art, design tokens, and capture scripts were created during this project session. Canvas art is seeded code, not a stock city asset. Third-party libraries and API data are permitted by the brief but retain their own licenses/terms.

- FastAPI, Pydantic, HTTPX, uvicorn, trafilatura, defusedxml, pytest, ruff: see installed package license metadata and `uv.lock`.
- TypeScript, Vite, esbuild, happy-dom: see package licenses and `frontend/package-lock.json`. Happy-dom is used for interaction tests, not as a real browser.
- Bricolage Grotesque and Source Serif 4: distributed locally via Fontsource, SIL Open Font License. Package license files are installed with the fonts; no remote font CDN is needed at runtime.
- Groq structured-output docs: https://console.groq.com/docs/structured-outputs
- ElevenLabs TTS and available voices: https://elevenlabs.io/docs/api-reference/text-to-speech/convert and https://elevenlabs.io/docs/api-reference/voices/search
- GNews search: https://docs.gnews.io/endpoints/search-endpoint
- NewsData latest: https://newsdata.io/blog/latest-news-endpoint/
- Google News RSS: links/attribution remain on every captured headline. This prototype is for personal/educational feed reading, not article redistribution. Check Google/publisher terms before public commercialization.

The JSON demo pack records authentic RSS headlines, publisher attribution, source links, capture time, and generated Groq analysis. Headline-only coverage is labeled; English search terms can return nonlocal outlets in foreign editions. Local-language refinement does not make the sample representative. No invented quote is accepted. An exact quote is not proof of interpretation accuracy.

Demo audio was generated through the configured ElevenLabs account and cached during the event. Voice assignments are dynamically selected from that account's available default voices; availability is not assumed from a fixed legacy voice list. Do not imply the voices are actual journalists or citizens of those countries. Review account redistribution rights before public publication.
