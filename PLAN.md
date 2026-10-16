# SCAM-KHEL — Plan

Deadline: Oct 30 2026 10:00 PDT (target "submitted" Oct 28 IST). Started Oct 16 → ~12 days.

## Phases (each ends: test + lint + typecheck + conventional commit)
| Phase | Scope | Days |
|---|---|---|
| P0 | Scaffold, config, CI, LICENSE, `.env.example`, secret scan, `llm/client.py`, `check_models.py` | 16–17 Oct |
| P1 | Taxonomy, rules, tagger, risk engine, sanitizer, injection filter, 20 fixtures | 17–19 |
| P2 | DB, Alembic, Fernet, script library, retrieval, learn, memory-hit | 19–20 |
| P3 | Persona, stalling, decoys, output guard, simulator (6+1 scenarios), orchestrator | 20–22 |
| P4 | Evidence extractor, Tavily verifier, complaint PDF/MD, blocklist | 22–23 |
| P5 | Telegram alerts, panic flow, alert log | 23–24 |
| P6 | API + WebSocket + Next.js frontend, i18n, Playwright | 24–27 |
| P7 | Voice (cut first if behind) | 27 |
| P8 | Evals, DEMO_MODE + replay, Docker, docs, audit | 27–28 |

Cut order if late: voice → vision input → extras. Never cut: tests, evals, safety, demo mode, docs.

## File tree
As specified in the build prompt §4 (monorepo `backend/` FastAPI + `frontend/` Next.js 14).

## Risks
- Nemotron model IDs on Token Factory unknown → `check_models.py` is the source of truth; env-driven IDs.
- Tool-calling reliability unknown → JSON-schema prompt protocol + pydantic + 2 repair retries is the default.
- Reasoning/`<think>` output → stripped before parsing.
- Secrets (Nebius, Tavily, Telegram) absent in dev → `--offline` mock adapter, `docs/MANUAL_STEPS.md`.
- Docker not installed on dev machine → compose files written but unverified locally (flagged in final report).
- Budget exhaustion on public demo → DEMO_MODE + replay.
- Dev git root: repo is initialised inside the project dir (the home dir is itself a git repo).
