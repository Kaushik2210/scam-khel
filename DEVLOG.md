# DEVLOG — friction with Nebius Token Factory / NVIDIA tools

Format: `YYYY-MM-DD — tool — detail`

- 2026-10-16 — Nebius Token Factory — No API key available in dev environment yet; `check_models.py` cannot validate model IDs. Pending user action (docs/MANUAL_STEPS.md).
- 2026-10-16 — openai Python SDK 3.x — Uses `httpx2` as its transport, so `respx` (httpx mocking) does not intercept calls; tests inject `DefaultAsyncHttpxClient(transport=httpx2.MockTransport(...))`. Cost ~30 min to diagnose.
- 2026-10-16 — Nebius Token Factory — NEBIUS_BASE_URL in the brief notes docs list more than one host; unverified. Model IDs, reasoning on/off switch, tool-calling reliability all UNVERIFIED (no key). `check_models.py` is ready to settle them.
- 2026-10-17 — Tavily (python client) — `AsyncTavilyClient.search` has a very wide signature (`include_domains`, `include_domains_mode`, `exact_match`, ...). `include_domains` confirmed present by inspecting the installed client; live behaviour unverified.
- 2026-10-17 — Next.js — 14.2.x (latest 14) still carried ~18 advisories (npm audit: 1 critical); only 16.x is clean, forcing React 19 + ESLint 9 flat config (`next lint` is gone). Done; 0 vulnerabilities.
- 2026-10-17 — Playwright — bundled Chromium would not launch on this Windows machine (`spawn UNKNOWN`); `PW_CHANNEL=msedge` works. Edge tears down the browser after a blob download, so the download test runs last and prints a harmless worker-teardown error; CI uses bundled Chromium.
- 2026-10-17 — Eval — first run of the held-out set found a false positive on a public scam-awareness advisory (held-out F1 0.917, FP rate 0.111). Fixed with an awareness-context dampener (post-hoc, disclosed in the report).
- 2026-10-19 — FastAPI File Uploads — `fastapi.File` requires `python-multipart`. To avoid adding extra dependencies and strictly guarantee zero disk persistence of user voice streams, implemented `POST /api/voice/transcribe` reading raw body bytes directly via `await request.body()` with a 2MB size cap.
- 2026-10-19 — Reverse Proxy Security — Trusting `X-Forwarded-For` by default allows client IP spoofing to bypass per-IP rate limits. Implemented `trusted_proxies` in `config.py` that parses right-to-left, stripping trusted hops and falling back to direct connection IP.
- 2026-10-19 — Structured Output Tools Mode — Mapped Pydantic schemas into OpenAI `tools` specification (`function` type + `tool_choice={"type": "function", ...}`). Implemented automatic fallback to JSON-prompt parser on tool-calling failure.

