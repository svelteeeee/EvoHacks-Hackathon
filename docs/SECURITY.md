# Security and privacy boundaries

This is an educational prototype, not a hardened multi-tenant production service.

- API credentials are read server-side from ignored `.env`, omitted from settings repr, never returned by config, and never bundled into the frontend. Do not enable verbose HTTPX logs: news request query parameters contain API keys.
- `.env.example` only contains placeholders. Credentials shared in chat are exposed and must be revoked/rotated before publication.
- Source/AI text is HTML-escaped before rendering. Only Pydantic-validated HTTP(S) source URLs are accepted. There is no client-side arbitrary HTML from articles.
- RSS XML uses defusedxml. Article extraction rejects local/private destination IPs, non-HTTP schemes, embedded credentials and nonstandard ports; redirect destinations are rechecked. **DNS validation and HTTP resolution are separate**, so sophisticated DNS-rebinding protection is not complete. Use an outbound egress allowlist/proxy before public hosting.
- News feed discovery only uses fixed provider endpoints. Article requests have size/time/redirect limits and preserve excerpts when unavailable.
- Concurrent API work is bounded. This is not per-client rate limiting or authentication: public visitors could exhaust credits. Add identity-based quotas and same-origin mutation checks before publishing live APIs publicly.
- Saved reports contain queries, headline/excerpt samples, AI analysis and source links. Treat those as public on a publicly deployed server; there are no private account reports.
- Demo mode does not call remote services; demo audio does not generate speech at runtime. Explicit preparation scripts may use credits.
- No article body is intentionally committed in demo fixtures. Check upstream feed licensing and ElevenLabs voice/account usage rights before redistribution.
