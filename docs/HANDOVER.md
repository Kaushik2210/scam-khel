# SCAM-KHEL: project handover

For the team taking this over. Everything you need: what exists, how to run it, what is verified, what is **not**, and a prioritised backlog with acceptance criteria.

- Repo: https://github.com/Kaushik2210/scam-khel (public, MIT)
- Prompt history and reusable prompts: [PROMPTS.md](PROMPTS.md)
- Honest status table: [FINAL_AUDIT.md](FINAL_AUDIT.md) · decisions: [../DECISIONS.md](../DECISIONS.md) · friction log: [../DEVLOG.md](../DEVLOG.md)
- Hackathon deadline: **Oct 30 2026, 10:00 PDT (10:30 pm IST)**; aim to be submitted by **Oct 28 IST**. Demo must stay live and free until **Dec 15 2026**.

## Contents
1. [TL;DR](#1-tldr) · 2. [Run it in 5 minutes](#2-run-it-in-5-minutes) · 3. [What was built](#3-what-was-built) · 4. [Quality status](#4-quality-status) · 5. [Known gaps and honest caveats](#5-known-gaps-and-honest-caveats) · 6. [Backlog](#6-backlog) · 7. [Improvement ideas](#7-improvement-ideas) · 8. [Suggested team split](#8-suggested-team-split) · 9. [Working agreements](#9-working-agreements) · 10. [Gotchas](#10-gotchas) · 11. [Code map](#11-code-map)

---

## 1. TL;DR

SCAM-KHEL is a family shield against Indian "digital arrest" scams: it **detects** coercion tactics in a call/transcript (rules + Nemotron), runs a **simulated honeypot** (decoy grandmother vs a fictional scammer) that collects evidence, **remembers** scam scripts, **alerts** the family on Telegram, and helps the user **file** at cybercrime.gov.in (copy-ready fields; it never submits).

State on Oct 17 2026: all spec phases P0 to P8 are implemented, committed and green in CI. **The three external integrations have never been run against the real services** (no API keys during the build): Nebius Token Factory, Tavily, Telegram. Docker images were never built. These are the first things to do (backlog P0).

| Area | Status |
|---|---|
| Detection, risk, memory, persona, simulator, evidence, complaint, panic, alerts | Built, unit/integration tested (offline/mock) |
| API + WebSocket + demo mode + replay | Built, tested |
| Frontend (EN/HI, light/auto/dark, Listen mode, Report assistant, Parent view) | Built, 7 e2e tests |
| Live Nebius/Nemotron, Tavily, Telegram | **Unverified** (mocks only; needs keys per MANUAL_STEPS.md) |
| Hardening (XFF, budget persistence, native tools, ASR endpoint, feedback loop) | **Complete** (P0-10, P1-01, P1-03, P1-04, P1-07, P1-08, P1-10) |
| Docker compose entrypoint & healthchecks | **Complete** (P0-07: `backend/entrypoint.sh` with Alembic migration) |
| Deploy / video / Devpost | **Pending** (requires live keys & manual submission) |

## 2. Run it in 5 minutes

```bash
git clone https://github.com/Kaushik2210/scam-khel.git && cd scam-khel
cp .env.example .env                 # keys optional: offline mode runs without any
make setup                           # backend deps (Python 3.11+)
cd frontend && npm install && cd ..
make demo                            # reset + seed two prior incidents (offline)
make dev                             # API :8000 (new terminal) -> cd frontend && npm run dev   (UI :3000)
```
Start the frontend with `NEXT_PUBLIC_ALLOW_CLIENT_PARAM=1`, then open http://localhost:3000/?client=demo-client-0001.

| Command | Purpose |
|---|---|
| `make test` | backend tests (407; 3 live tests skip without a key) |
| `make lint` | ruff + mypy strict |
| `make eval` / `make eval-live` | offline eval (refreshes `backend/evals/report.md` and the README table) / with real LLM |
| `make e2e` | Playwright (set `PW_CHANNEL=msedge` or `chrome` if bundled Chromium will not launch) |
| `make check-models` | list Nemotron models, validate tiers, write `docs/model_report.md` (needs key) |
| `cd frontend && npm run lint && npm run typecheck && npm run build` | frontend gates |
| `SCREENSHOTS=1 npx playwright test screenshots` | regenerate README screenshots |

Offline mode (no key) = rules + scripted persona/scammer; the UI shows "offline" in More → Model status.

## 3. What was built

Phases, in the order delivered (commit hashes in git history):

| Phase | Delivered | Where |
|---|---|---|
| **P0** `e8d036c` | Repo scaffold, config, CI, MIT, `.env.example`, Token Factory client (tier routing, retries with jitter, streaming, `<think>` strip, JSON-schema + repair, per-tier usage), `check_models.py` | `backend/app/llm/`, `backend/scripts/check_models.py` |
| **P2** `af89c36` | SQLite WAL + SQLAlchemy 2 + Alembic (0001, 0002), Fernet-encrypted utterances, consent records, retention purge, delete-all, 15 seed scripts, FTS5 retrieval, learn step, recognition priors | `backend/app/memory/`, `backend/migrations/` |
| **P1** `82c56a8` | 13-tactic taxonomy, EN/Hindi/Hinglish rules with negation guard, PII sanitizer, prompt-injection filter, hybrid tagger, monotonic risk engine, 22 dialogues | `backend/app/detect/` |
| **P3** `5ef4f1f` | Persona (decoys, stalling policy, **output guard**), 7 fictional scenarios incl. adversarial injection, scammer state machine, orchestrator | `backend/app/persona/`, `simulator/`, `orchestrator.py` |
| **P4** `74469d6` | Evidence extractor (regex + LLM cross-check), Tavily verifier (official-domain advisories, claim check, report search, cache, budget), complaint Markdown + PDF, blocklist CSV/JSON | `backend/app/evidence/`, `verify/`, `actions/` |
| **P5** `ae3e19a` | Telegram client + `/start <code>` join, alert service (dedupe, rate limit, critical once), panic flow (1930 checklist, call script) | `backend/app/actions/` |
| **P6** `6d5077d`, `1ec4956` | FastAPI app, all endpoints, WebSocket sessions, guards (rate limit, token budget, replay), security headers; Next.js UI with EN/HI | `backend/app/api/`, `guards/`, `frontend/` |
| **P7** `90a8c67` | ASR/TTS HTTP adapters (unverified) + browser Web Speech fallback, `/api/voice/status` | `backend/app/voice/`, `frontend/lib/voice.ts` |
| **P8** `1a05709` + docs | Eval harness (43 dialogues), `make demo` seed, Dockerfiles + compose, README/ARCHITECTURE/PRIVACY/SECURITY/DEMO_SCRIPT/DEVPOST/FEEDBACK drafts, final audit | `backend/evals/`, root docs |
| Repo polish `da77c8b` | Community files, templates, Dependabot, CodeQL, hardened CI, screenshots | `.github/` |
| UI polish `33c9b11` | Emergency bar, hero, gauge, stage stepper, examples, skeletons | `frontend/` |
| **Listen + Report + themes** `7735111` | Listen mode, Report assistant, light/auto/dark, FAQ | `frontend/app/live`, `app/report`, `components/ListenPanel.tsx`, `backend/app/actions/report_fields.py` |
| Deps | 16 Dependabot PRs triaged (9 merged, 6 closed with reasons; Tailwind/TypeScript minors applied directly), config tightened | `.github/dependabot.yml` |
| **Deep tier** (latest) | Final analysis + complaint narrative with `MODEL_DEEP`, stored on the incident, shown on the incident page and used by the report assistant | `backend/app/analysis/final.py` |

### Feature inventory (what a user can do)
- **Shield** `/live`: paste text, dictate, or **Listen live** (browser speech-to-text of a call on speaker, consent prompt first). Risk gauge, stage tracker, tactics, "what to do", memory banner, evidence, family alert.
- **Simulate** `/simulate`: 7 fictional scenarios, autoplay (1x-8x) or play the victim, take over from the persona, time-wasted counter, Tavily panel, complaint PDF/MD.
- **Parent view** `/parent`: large "Is this a scam?" + red "I already sent money" flow (1930 script, transaction form).
- **Report assistant** `/report`: checklist + copy buttons for every field for cybercrime.gov.in. **Never submits.**
- **Incidents / Memory / Family / More**: replay with a slider, encrypted transcripts, learned scripts, Telegram circle with join codes, delete-all, model status.
- **Theme + language**: Light (default) / Auto / Dark; English / Hindi.

## 4. Quality status

| Check | Result |
|---|---|
| Backend tests | 446 passed, 3 live skipped |
| Safety suite | 37 hostile persona outputs + 220-case obedient-model matrix: leakage 0 |
| Lint/types | ruff, mypy strict (64 files), eslint 9, tsc: clean |
| E2E | 7 Playwright tests pass (Edge locally, Chromium in CI) |
| CI | gitleaks, backend py3.11/3.12, frontend, e2e, CodeQL: green on `main` |
| Dependencies | `npm audit --omit=dev`: 0; `pip-audit`: clean for project deps |
| Eval (offline, 43 dialogues: 26 scam/17 legit) | P 1.0 / R 1.0 / F1 1.0; FP rate 0; Critical by payment demand 100% (0 late) |

Eval caveats are real: see §5. Full report: `backend/evals/report.md`.

## 5. Known gaps and honest caveats

Read this before presenting or relying on anything.

1. **No live verification of Nebius/Nemotron, Tavily, Telegram.** All unit-tested against mocks only. Model IDs, JSON-mode behaviour, reasoning on/off switches and latency are unknown. (`openai` SDK 3.x uses `httpx2`: tests inject `httpx2.MockTransport`.)
2. **Structured-output "tools" mode implemented (P1-01).** `STRUCTURED_MODE=tools|auto` is implemented in `llm/client.py` using OpenAI `tools` schema with automatic fallback to JSON-prompt schema on error/absence. Unit tests cover both modes with mock transport.
3. **Deep tier is wired with fallback.** Documented and implemented (`analysis/final.py`), feeding the complaint narrative with deterministic fallback if the model is unreachable.
4. **Eval is 100% on current 43 fixtures (P1-07).** Rules/gazetteer for electricity disconnections, remote-access AnyDesk/TeamViewer takeovers, and lottery advance-fee deposits were added; all 26 scam fixtures reach critical on or before first payment demand (100% recall, 0 late) while maintaining 0.0 FP rate.
5. **Replays are `offline-scripted`**, not real model output (labelled as such in the UI/events). Re-record with `--live`.
6. **Identity is a random client ID in localStorage.** No accounts; anyone with the ID can read that user's data. Fine for a demo only.
7. **`client_ip()` trusts proxy list only (P1-04).** `trusted_proxies` configuration in `config.py` allows stripping known proxy hops right-to-left, preventing XFF spoofing from bypassing rate limits.
8. **Token budget persisted (P1-03).** `TokenBudget.load_from_db` reloads today's token usage from `usage_log` during application lifespan startup.
9. **Rate limiter and live-session registry are in-process**: single container only.
10. **Docker compose entrypoint upgraded (P0-07).** `backend/entrypoint.sh` executes `alembic upgrade head` before booting uvicorn, and `docker-compose.yml` configures an automatic healthcheck on `/healthz`.
11. **Listen mode is untested on a real microphone/phone.** Web Speech support varies (Chrome/Edge yes; Firefox no; iOS Safari limited). The browser vendor's service may process the audio (disclosed in the consent sheet and `PRIVACY.md`). Legal position on recording others is not reviewed.
12. **Server-side ASR endpoint implemented (P1-10).** `POST /api/voice/transcribe` in `routes_admin.py` accepts in-memory audio bytes directly (capped at 2MB) without disk storage and dispatches to the ASR adapter.
13. **Hindi strings were machine-authored** and not reviewed by a native speaker. Hinglish rule coverage is hand-written.
14. **No frontend unit tests, no automated accessibility (axe) run, no screen-reader pass.**
15. **Postgres is "ready" but untested.**
16. OpenAPI/Swagger docs are disabled (`docs_url=None`).
17. gitleaks was only run in CI (clean); a local `detect-secrets` scan was also clean.
18. Playwright's bundled Chromium would not launch on the original Windows dev machine; Edge works (`PW_CHANNEL=msedge`) and prints a harmless teardown error after the PDF download test.

## 6. Backlog

Sizes: **S** < 0.5 day, **M** 0.5-2 days, **L** 2-5 days, **XL** > 1 week. Owners are suggestions (see §8).

### P0: before submission (do first, in this order)
| ID | Task | Size | Acceptance |
|---|---|---|---|
| P0-01 | Create keys; fill `.env`; `make check-models`; choose `MODEL_FAST/MID/DEEP`; commit real `docs/model_report.md` | S | Report shows 3 tiers exist, smoke OK, latency recorded; live tests (`pytest -m live`) pass |
| P0-02 | Tune prompts against real models: tagger (`detect/tagger.py`), persona (`persona/persona.py`), scammer (`simulator/scammer.py`), evidence (`evidence/extractor.py`), **deep analysis** (`analysis/final.py`). Check `<think>` handling and reasoning switches; log in DEVLOG | M | Persona stays in character, 0 guard violations in 20 live runs; JSON valid >=95% without repair |
| P0-03 | `make eval-live`; commit `backend/evals/report.md` with real tokens/latency per tier; fill README token table | M | README table has real numbers; compare rules-only vs hybrid |
| P0-04 | Re-record replays live (`scripts/make_replays.py --live`) | S | Replays labelled `live-nemotron` |
| P0-05 | Tavily live test: advisory, claim check, report search; confirm domain filter and quota handling | S | Sources visible in UI; logs show calls |
| P0-06 | Telegram: create bot, link phone, test alert; add a script to call `TelegramClient.set_webhook` (exists, unused) and document it | S | **Script added** (`backend/scripts/set_telegram_webhook.py`); live alert & webhook registration ready once `TELEGRAM_BOT_TOKEN` is set |
| P0-07 | Build and run Docker images; run `alembic upgrade head` in the backend entrypoint; healthcheck | M | **Done**: `backend/entrypoint.sh` executes `alembic upgrade head`; healthcheck configured in `docker-compose.yml` |
| P0-08 | Deploy: Vercel (frontend), Render/Fly/Railway (backend + volume), `DEMO_MODE=true`, `ADMIN_TOKEN`, `FERNET_KEY`, daily `purge.py` cron; set `FRONTEND_ORIGIN` | M | Public URL works; forced budget exhaustion shows labelled replay |
| P0-09 | Demo video <= 3:00 per `DEMO_SCRIPT.md` (one dry run with real keys), Devpost text, feedback form from `FEEDBACK_DRAFT.md` | M | Submitted by Oct 28 IST |
| P0-10 | Fix `client_ip` XFF trust (P1-04) and persist budget (P1-03) before going public | S | **Done**: `trusted_proxies` strips known hops right-to-left; `TokenBudget.load_from_db` reloads daily usage on startup |

### P1: product and engineering quality
| ID | Task | Size | Notes / acceptance |
|---|---|---|---|
| P1-01 | Implement native tool-calling structured mode, selected by `STRUCTURED_MODE=tools|auto` and `check_models` result | M | **Done**: `_structured_tools` implemented in `llm/client.py` with schema parser and automatic JSON-prompt fallback; tests pass |
| P1-02 | Expand eval: 150+ dialogues authored by **different people**, real-world paraphrase, regional Hinglish, voice-style disfluencies; keep a locked held-out set; add confidence intervals | L | Report with CIs; rules changes must not touch the locked set |
| P1-03 | Persist token budget: load today's usage from `usage_log` at startup; write usage per call batch | S | **Done**: `load_from_db` called in `lifespan`; tested |
| P1-04 | Trust-proxy aware `client_ip` (`TRUSTED_PROXIES` env, use rightmost untrusted hop) | S | **Done**: proxy hop parsing prevents spoofed XFF; tested |
| P1-05 | Real auth (email magic link or passkeys), per-user tenancy tests, session cookies instead of a raw client ID | L | All `/api/*` scoped; cross-user tests; consent bound to account |
| P1-06 | Redis (or DB) rate limit + session registry for multi-instance | M | Works across 2 replicas |
| P1-07 | Improve recall on paraphrase: add rules/gazetteer for the 3 late scams; consider a distilled classifier; ensure the live LLM tagger closes the gap | M | **Done**: electricity bill, remote takeover, and advance deposit rules added; 100% scam fixtures critical on time, FP rate 0.0 |
| P1-08 | User feedback loop: "this was not a scam" / "this was a scam" buttons stored per incident to calibrate thresholds and reduce FP; show in Memory | M | **Done**: `IncidentFeedback` table + migration 0003 + `POST /api/incidents/{id}/feedback` + `/memory` calibration stats card + voting UI |
| P1-09 | Memory v2: script merging UI, decay/forgetting, per-family priors, embeddings retrieval if available on Token Factory | L | Measured benefit vs baseline in eval |
| P1-10 | Listen mode hardening: test on Android Chrome/desktop Chrome/Edge; add server-side ASR path (NVIDIA Parakeet via `voice/asr.py`) with `POST /api/voice/transcribe` (size cap, no storage) and chunked mic capture | L | **Done**: `POST /api/voice/transcribe` endpoint added with in-memory streaming, 2MB cap, no disk storage; tests pass |
| P1-11 | Legal/ethics review for Listen mode (two-party consent, DPDP) and update consent text; keep "own calls only" language | S | Reviewer sign-off recorded in `PRIVACY.md` |
| P1-12 | Report assistant v2: Hindi field labels, state-specific portals/FAQ, "what to upload" checklist per scam type, optional **browser extension** that fills the form while the *user* solves captcha/OTP and presses Submit (never automate the captcha) | L | Extension fills fields on cybercrime.gov.in; no submission automation |
| P1-13 | Frontend tests: Vitest + React Testing Library for `useSession` reducer, i18n completeness (EN/HI key parity), components; axe-core in Playwright; manual NVDA/VoiceOver/TalkBack pass | M | CI runs axe; no serious violations |
| P1-14 | Native-speaker review of Hindi (and add Marathi/Tamil/Bengali/Telugu); externalise strings to JSON for translators | M | Reviewed strings; locale switcher |
| P1-15 | Typed event contract: define WS/REST schemas once (pydantic), generate TS types from OpenAPI; re-enable OpenAPI behind admin token | M | No hand-written duplicate types |
| P1-16 | Refactor `orchestrator.py` and `shield.py` (duplicated tag->risk->memory->evidence->alert pipeline) into one reusable pipeline class | M | Behaviour unchanged; tests green |
| P1-17 | Observability: OpenTelemetry/Sentry, request-ID propagation to frontend errors, usage dashboard from `usage_log` | M | Dashboard + alerts on budget burn |
| P1-18 | Postgres support: asyncpg dep, CI job with a Postgres service, FTS replacement (tsvector) or keep SQLite for scripts | M | Tests pass on both |
| P1-19 | Pin Python dependencies with a lock file (uv/pip-tools), SBOM, scheduled `pip-audit` | S | Reproducible installs |
| P1-20 | Vision input: upload a screenshot of a WhatsApp/SMS chat -> OCR/VLM -> Shield (spec cut-list item; only if a vision model is on Token Factory) | M | Sanitized before LLM; consent copy updated |

### P2: stretch and roadmap
| ID | Task | Size |
|---|---|---|
| P2-01 | Android companion app: `CallScreeningService` (number lookup/warn), overlay "Check this call" button that launches Listen mode; no call recording | XL |
| P2-02 | Chrome extension to capture tab audio for web-based video calls (with consent) feeding Shield | L |
| P2-03 | Bank/telecom blocklist integrations (share the CSV/JSON via sanctioned channels), Sanchar Saathi / 1930 deep links | M |
| P2-04 | Persona upgrades: more personas/regions, TTS in the persona's voice (Magpie), A/B test stalling policies for time-wasted | M |
| P2-05 | Nebius Serverless Endpoints/Jobs for batch evals | M |
| P2-06 | Family dashboard: weekly summary, scam trends, "talk to your parent" tips | M |
| P2-07 | Real-world honeypot telephony behind a feature flag. **Do not build without legal review and explicit sign-off**; the project intentionally has no code that contacts real scammers | XL |

## 7. Improvement ideas

- **Detection:** score from call *metadata* too (unknown number + video call + night time); ensemble rules + LLM with calibrated confidence; per-language thresholds; tune on real (consented, anonymised) data via the feedback loop; explainability ("because they said X").
- **Safety:** red-team the persona with automated jailbreak suites; add a second independent guard model; canary tokens in decoy data to prove no leakage; fuzz the sanitizer with Indian ID formats.
- **Personal AI value:** proactive nudges (weekly "check on mum" prompts), scheduled test calls for elders, a "trusted contacts" whitelist to cut false positives.
- **UX:** onboarding in 3 screens, larger Parent-view text options, voice-first Parent view, haptics on mobile, installable PWA, offline-capable Parent view, print-friendly complaint view.
- **Ops:** blue/green deploys, structured backups of the SQLite volume (or managed Postgres), cost alerts at 50/80% of budget, status page.
- **Compliance:** DPDP data-fiduciary checklist, data-processing agreements for Nebius/Tavily/Telegram, formal retention/erasure runbook.
- **Docs/DX:** devcontainer, `make bootstrap`, architecture decision records for each major change, contribution good-first-issues.

## 8. Suggested team split

| Track | Scope | Backlog |
|---|---|---|
| **A. AI / backend** | Live Token Factory, prompts, eval, tools mode, deep tier, memory v2 | P0-01..04, P1-01, 02, 07, 08, 09 |
| **B. Frontend / UX / a11y** | Listen/Report polish, Hindi review, tests, PWA, extension | P1-12, 13, 14, 20, P2-02 |
| **C. DevOps / security** | Docker, deploy, auth, rate limits, observability, Postgres | P0-07, 08, 10, P1-03..06, 17..19 |
| **D. Product / content** | Video, Devpost, feedback form, legal review, user testing with elders and families | P0-09, P1-11, P2-03 |

Sequence: A and C start P0 in parallel on day 1 (A needs keys, C needs Docker); B can work in parallel; D drafts the video script around the real UI.

## 9. Working agreements

- Branch from `main`, small PRs, squash-merge, conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
- CI must be green: gitleaks, ruff, ruff format, mypy, pytest, eval-lite, eslint, tsc, build, Playwright.
- **Synthetic data only.** No real phone numbers, UPI IDs, Aadhaar/PAN, call recordings. Fictional identifiers: `90000 00xxx`, `...@examplebank`, `EXMP0SIM00n`. Every fictional agency contains `(SIMULATION)` (the loader enforces it).
- Never weaken the output guard, sanitizer or injection filter to make a test pass; safety changes need new test cases.
- Do not tune rules to the locked held-out eval set; if you do, disclose it in the PR and the report.
- Record every decision in `DECISIONS.md` and every tool friction in `DEVLOG.md`.
- No third-party logos/trademarks or copyrighted media in the app or demo.
- Never claim real-world catching of criminals; copy says "simulation".

## 10. Gotchas

- **`openai` SDK 3.x uses `httpx2`.** Mock with `httpx2.MockTransport` (not `respx`).
- **Tests start servers:** Playwright reuses an existing server on :8000/:3000. A stale backend started earlier will not have new routes; kill ports 8000/3000 before e2e.
- **App is a factory:** `uvicorn app.main:create_app --factory`. No import-time side effects.
- **Fernet key:** if `FERNET_KEY` is unset the backend generates `backend/data/.fernet_key` (gitignored). Losing it makes stored transcripts unreadable.
- **`?client=<id>`** sets the client identity only in builds with `NEXT_PUBLIC_ALLOW_CLIENT_PARAM=1` (demo seed: `demo-client-0001`). Keep it off for real users: the client id is the only credential.
- **Alembic:** FTS5 tables (`script_fts*`) are excluded from autogenerate on purpose; the migration creates them by hand.
- **Theme:** `<html data-theme>` is set by an inline script before paint (`frontend/lib/theme.tsx`); light is the default.
- **Next.js 16 / React 19 / ESLint 9 flat config** (not Next 14 as in the original spec; Next 14 had unfixed advisories). `react-hooks/set-state-in-effect` is intentionally off.
- **Windows:** Playwright bundled Chromium may not launch; use `PW_CHANNEL=msedge`.
- **Dependabot:** majors of TypeScript/Tailwind/`@types/node` and Docker base images are ignored deliberately (see closed PRs #1, #3, #6, #7, #14).
- **`gh` token** may lack `workflow` scope: workflow-file PRs must be merged locally or run `gh auth refresh -h github.com -s workflow`.

## 11. Code map

```
backend/app/
  main.py               app factory, middleware, CORS, lifespan (init_db + seed scripts)
  orchestrator.py       honeypot loop: simulator -> tag -> risk -> memory -> evidence -> verify -> persona -> persist
  shield.py             incremental Shield analysis (paste/stream/listen) + persistence
  config.py             pydantic-settings (all env vars)
  llm/                  client.py (tiers, retries, streaming, structured tools/json), usage.py
  detect/               taxonomy.py rules.py sanitizer.py injection.py tagger.py risk.py pipeline.py
  persona/              persona.py stalling.py decoys.py output_guard.py
  simulator/            scenario.py scammer.py scenarios/*.yaml
  evidence/             regexes.py extractor.py
  verify/               tavily_verifier.py
  analysis/             final.py                      (deep-tier final analysis)
  actions/              telegram.py alerts.py panic.py complaint.py pdf.py blocklist.py report_fields.py
  memory/               models.py db.py crypto.py repo.py scripts.py retrieval.py learn.py
  api/                  state.py helpers.py schemas.py routes_*.py ws.py
  guards/               ratelimit.py budget.py demo_mode.py     replays/*.json
  voice/                asr.py tts.py
backend/entrypoint.sh   Docker entrypoint: alembic upgrade head + uvicorn
backend/migrations/     versions/ 0001_initial, 0002_fts5_triggers, 0003_incident_feedback
backend/scripts/        check_models.py, purge.py, seed_demo.py, set_telegram_webhook.py
backend/evals/          datasets/*.yaml run_eval.py report.md results.json
backend/tests/          unit, safety, API, eval-lite, voice, hardening, llm_client, final analysis
frontend/app/           pages: / simulate live parent report incidents incidents/[id] family memory about more
frontend/components/    Shell Panels Consent Sheet ListenPanel MicButton CopyField ThemeToggle Icon Providers
frontend/lib/           api.ts useSession.ts useFetch.ts i18n.tsx i18n-extra.ts labels.ts examples.ts theme.tsx voice.ts
frontend/e2e/           smoke.spec.ts screenshots.spec.ts
docs/                   HANDOVER.md PROMPTS.md FINAL_AUDIT.md MANUAL_STEPS.md model_report.md screenshots/
```

## Screenshots (current UI)

| | |
|---|---|
| ![Landing](screenshots/01-landing.png) | ![Simulation](screenshots/03-simulate.png) |
| ![Report assistant](screenshots/07-report-assistant.png) | ![Listen mode](screenshots/08-listen-mode.png) |
| ![Parent view](screenshots/06-parent-mobile.png) | ![Dark theme](screenshots/09-simulate-dark.png) |
