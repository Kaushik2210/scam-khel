# Security

## Reporting
Open a private security advisory on the repository, or email the maintainer. Please do not file public issues for vulnerabilities.

## Controls implemented (and tested)
| Area | Control | Where / test |
|---|---|---|
| Secrets | env only; `.env` ignored; `.env.example`; gitleaks in CI + pre-commit; local `detect-secrets` scan of files and a history grep were clean | `.github/workflows/ci.yml` |
| Input | pydantic validation, 64 KB body cap, per-field length caps, WS message cap, path-traversal-safe scenario/replay loaders | `tests/test_api.py` |
| Abuse | per-IP sliding-window limits (sessions, analyze, panic), global daily token budget, max turns | `app/guards/` |
| Prompt injection | heuristics + classifier prompt; untrusted text delimited and never placed in system prompts; neutralised before reuse | `app/detect/injection.py`, `tests/test_detect.py`, `tests/test_persona_safety.py` |
| Output | persona output guard (PII, OTP, UPI, compliance, AI-reveal, length) with clean rewrite | `app/persona/output_guard.py`; 37 hostile outputs + 220-case matrix |
| Privacy | PII sanitizer before LLM, Fernet at rest, retention purge, delete-all | `app/detect/sanitizer.py`, `app/memory/` |
| Transport/web | CORS locked to `FRONTEND_ORIGIN`; security headers (API and frontend CSP, nosniff, frame deny, no-referrer); WS origin check | `app/main.py`, `frontend/next.config.mjs` |
| AuthZ | per-client isolation (all queries scoped to the client's user); admin usage and Telegram webhook need constant-time-compared secrets | `tests/test_api.py` |
| Exports | CSV formula-injection neutralised; PDF/Markdown redact personal data by default | `app/actions/` |
| Logs | PII redaction, no tokens (Telegram token never logged) | `app/logging.py`, `tests/test_p5.py` |

## Known gaps / accepted risk
- **Identity model:** a random client ID in `localStorage` identifies a user. There are no accounts or passwords, so anyone holding that ID can read that user's data. Fine for a demo; add real auth before production.
- Rate limiting and live-session registry are in-process (single container). Use Redis for multi-instance.
- `pip-audit` was clean for project dependencies after raising the Pillow floor; other findings were in unrelated tooling in the dev environment. `npm audit --omit=dev`: 0 vulnerabilities after moving to Next 16.
- LLM-based detection can be wrong or evaded; rules plus the output guard are the safety backstop for the persona, not the model.
- Docker images and the live Token Factory, Tavily and Telegram integrations were not exercised against real services in this build.
