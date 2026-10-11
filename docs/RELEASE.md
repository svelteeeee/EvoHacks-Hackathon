# Release checklist

## Browser checks — pending user review
- [ ] Inspect desktop 1440px and phone 390px: no clipped controls or unintended horizontal overflow.
- [ ] Fresh session: city wakes in ~5.5 seconds; click/key/Skip work. Same-session refresh skips intro.
- [ ] Reduced motion: static lit city. Hidden tab: animation pauses and resumes without jumping.
- [ ] Cmd/Ctrl+K, arrow/Enter selection, Tab navigation, visible focus, Esc/dialog focus return.
- [ ] All three cached events in English/Spanish/French; original headlines, simple summary, citations.
- [ ] Select each theme; district brightness agrees with numeric matrix. Hover focuses matching sources. Click nonzero cells and inspect exact quotes.
- [ ] Listen to English audio: COP28 summary/US/UK/France; Moon/Olympics all seven tracks. Other combinations honestly say unavailable. No autoplay.
- [ ] Print/Save as PDF: summary, source labels and matrix remain readable.
- [ ] Check browser console/network for errors and proper HTML/JS/CSS/font/audio content types.
- [ ] Test without network after local server/dependencies are ready; demo requests never call providers.
- [ ] Rerun live smoke after Groq quota resets; final full-text verification is currently blocked.

## Performance
Measure on a mid-range laptop before claiming 60fps. Record DevTools Performance during intro and results; target <=16.67 ms total frame budget. `window.newsBridgePerformance` reports CPU canvas draw p95, not complete frame time. Write hardware, viewport, browser, frame p95 and dropped frames to `docs/browser-performance.md`.

## Screenshots / video / public repo
Actual media capture is pending. Save real landing/comparison screenshots to `docs/screenshots/landing.png` and `docs/screenshots/comparison.png`, or record a short real GIF; add links to README. Record the 2:30 walkthrough from `DEMO.md`, showing features AND code. A script is not a video.

Rotate exposed keys; keep replacements in ignored `.env`. Run tests/typecheck/build/contrast/HTTP verification, inspect changes, then authorize commit/push. Verify GitHub public visibility before submitting. Use README local run steps unless public Python hosting is explicitly requested; the private preview is not a public deployment. Add visitor quotas before public live API access.

## Cloud restart
Archive/restore may remove dependencies and processes. Reinstall with `uv sync --locked` and `npm --prefix frontend ci`. Restart FastAPI and Vite. Bind Vite to 0.0.0.0:3000 and allow only the current exact preview hostname through `__VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS`; never `allowedHosts: true`. Reopen the preview panel.
