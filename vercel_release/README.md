# News Bridge (Vercel static build)

This is the production-ready static build of News Bridge, ready to deploy to
Vercel. It includes no backend — all AI analysis (translation, framing,
clustering, narration) runs server-side, so this is the frontend only.
For a self-hosted version with the pipeline API, use the `release_package/`
zip instead.

## Deploy to Vercel

1. Push this `vercel_release/` directory to a GitHub repo (or use the zip).
2. Import the repo in Vercel.
3. Set root directory to the repo root (where `vercel.json` lives).
4. Deploy.

No environment variables are required — the package runs in cached-demo mode
with no live keys, so it works out of the box.

## What's included

- `index.html` — app entry point
- `assets/` — bundled JS, CSS, and locally-hosted fonts
- `vercel.json` — static hosting config
- `README.md` — setup notes
