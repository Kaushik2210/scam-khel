# Changelog

All notable changes are documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

## [0.1.0] - 2026-10-17

First hackathon release (Nebius x NVIDIA Global AI Hackathon, Personal AI track).

### Added
- Tier-routed Nebius Token Factory client (retries, streaming, `<think>` stripping, JSON-schema repair, per-tier usage accounting) and `check_models.py`.
- Hybrid scam detector (English / Hindi / Hinglish rules plus a Nemotron tagger), PII sanitizer, prompt-injection filter, monotonic risk engine.
- Encrypted memory (SQLite, FTS5, Alembic), script learning and a memory-hit risk prior.
- Honeypot persona with an output guard, 7 fictional scenarios (including an adversarial one), evidence extraction, Tavily verification.
- Telegram family alerts, complaint PDF/Markdown, blocklist export, panic flow.
- FastAPI + WebSocket API, DEMO_MODE with a token budget and replay fallback; Next.js UI (EN/HI, Parent view); voice through the browser Web Speech API.
- Eval harness (43 dialogues), 400+ backend tests, Playwright smoke tests, CI, CodeQL, Dependabot.

### Known limitations
Simulation only. Live Token Factory, Tavily and Telegram paths are verified against mocks only. See `docs/FINAL_AUDIT.md`.
