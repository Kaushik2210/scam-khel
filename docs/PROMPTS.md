# Prompt log

Every instruction given to the AI coding assistant (Claude Code) while building SCAM-KHEL, in order, with what was done in response. Use this to understand *why* things are the way they are, and to reuse the prompts for follow-up work.

- Companion doc: [HANDOVER.md](HANDOVER.md) (status, backlog, how to continue).
- Dates are 2026-10-16 to 2026-10-17 (the whole build took two days of assistant time).
- A global instruction was also active throughout (user's `~/.claude/CLAUDE.md`): *"For any UI work, apply Apple Human Interface Guidelines using the `hig-*` skills first, translated to the web (semantic colours, 44px targets, visible focus, light/dark, reduced motion)."* That is why the UI follows HIG-style tokens.

---

## Prompt 1: the master build spec (verbatim)

> Everything below is exactly what was pasted, including its numbering. It is the source of truth for scope. Where the build deviated, see [HANDOVER.md §5](HANDOVER.md#5-known-gaps-and-honest-caveats) and [DECISIONS.md](../DECISIONS.md).

```text
SCAM-KHEL — END-TO-END BUILD PROMPT FOR CLAUDE CODE
You are the lead engineer building SCAM-KHEL, a production-quality entry for the Nebius x NVIDIA Global AI Hackathon (Personal AI track). Submission deadline: Oct 30, 2026, 10:00 am PDT (10:30 pm IST). Target "submitted" by Oct 28 IST. Read this ENTIRE document before writing any code.
0. HOW YOU MUST WORK

1. First, create `PLAN.md` (phases, file tree, risks) and `DECISIONS.md` (every non-obvious choice + reason). Then execute phase by phase (Section 14).
2. Use your task list. After each phase: run the full test suite, lint, type-check, then `git commit` (conventional commits). Never leave the main branch broken.
3. Do NOT ask me questions unless you are truly blocked (missing API key, model ID not found). Otherwise decide, record in `DECISIONS.md`, and continue. If blocked on a secret, build everything else with a mock adapter and list exactly what I must do in `docs/MANUAL_STEPS.md`.
4. No placeholder code, no `TODO` stubs, no fake data on the main path. Every feature ships with tests. Mocks are allowed ONLY in tests and in a clearly flagged `--offline` dev mode.
5. Keep `DEVLOG.md`: every time Nebius Token Factory or an NVIDIA model/tool gives you friction (docs gap, model ID mismatch, latency, rate limit, odd output, onboarding step), log it with date + detail. I will use it to fill the mandatory hackathon feedback form.
6. Prefer boring, well-known libraries. Time budget is ~12 days. If behind schedule, cut in this order: voice (Phase 7) → screenshot/vision input → optional extras. NEVER cut: tests, evals, safety layer, demo mode, docs.

1. PRODUCT
One-liner: A private, always-on family shield against Indian "digital arrest" scams that (a) detects coercion tactics in real time, (b) can hand the call to an AI "confused elder" honeypot that wastes the scammer's time and extracts evidence, (c) alerts the family and (d) drafts a ready-to-review complaint for the National Cyber Crime Reporting Portal (cybercrime.gov.in) with a reminder to call helpline 1930 immediately if money was sent.
Context facts (for copy and prompts; do not invent others): Fraudsters impersonate police/CBI/ED/customs, claim the victim or family is implicated in a crime, keep them "visible" on a video call, isolate them ("don't tell anyone"), and demand transfers to a "safe/verification account". Indian authorities state that police/CBI/ED/courts do not arrest people over video calls. Reporting channels: helpline 1930 and https://cybercrime.gov.in.
Modes

* Shield (detect): user pastes/speaks/streams a transcript of a suspicious call or message. System scores risk live, tags tactics, explains in plain Hindi/English, alerts the family circle.
* Honeypot (bait): an AI persona takes over the conversation text/voice channel inside the app and stalls a scammer while evidence is extracted. In this build the counterpart is a built-in scammer simulator (see 6.4). Real-world bait-line integration (e.g., telephony) is documented as future work only, disabled, behind a feature flag, with consent notice. DO NOT build code that contacts real scammers or real phone numbers.
* Parent View: a very simple large-button UI for elderly users: "Is this a scam?" (paste/speak) and a big red "I already sent money" panic flow.

2. HACKATHON HARD CONSTRAINTS (non-negotiable)

* Runtime LLM calls MUST go to Nebius Token Factory (OpenAI-compatible API). No other LLM provider at runtime (no HuggingFace Inference / OpenRouter / OpenAI / Anthropic calls in app code).
* MUST use NVIDIA open models: Nemotron via Token Factory. Tiering: fast/cheap model for per-utterance tagging, mid model for persona + orchestration, strongest model for final analysis/complaint. Model IDs come from env vars, never hard-coded (Section 5).
* Public GitHub repo, MIT license (LICENSE file at root; license must be detectable by GitHub). README with setup + clear callouts of where Nemotron, Token Factory and Tavily are used.
* Working hosted demo URL that stays free and unrestricted until Dec 15, 2026 → build a budget-protected DEMO_MODE (Section 12).
* Runtime Tavily call in the verification path (qualifies for Best Use of Tavily bonus).
* Personal AI track proof: persistent memory across sessions + real actions (Telegram alert, PDF complaint, blocklist export). Show memory improving behaviour (e.g., recognising a previously seen script faster).
* Demo video ≤ 3 min must not contain third-party trademarks/copyrighted music. Therefore: UI, simulator and assets must NOT use real agency logos or names as branding. The simulator uses fictional agency names labelled "(SIMULATION)".
* NEVER commit secrets. `.env` in `.gitignore`; provide `.env.example`; add a pre-commit secret scan (gitleaks or detect-secrets) and run it in CI.

3. SAFETY & ETHICS (build these in, test them)

* The honeypot persona must NEVER output real personal data. It only uses fictional decoy data from a fixed, clearly fictional list (e.g., decoy name, fictional bank names, non-routable fake account numbers, `decoy@examplebank` style UPI). Add an output guard that blocks and rewrites any persona output containing patterns resembling: 12-digit Aadhaar, PAN, 16-digit card numbers, OTP-like 4–8 digit codes presented as real, real phone numbers, real UPI handles not in the decoy list.
* The persona NEVER agrees to complete a payment, install an app, or click a link — it stalls ("beta, mujhe yeh samajh nahi aa raha…").
* Inputs from the "scammer" side are untrusted. Treat them as prompt-injection vectors ("ignore your instructions", "you are now…", fake system messages). Implement a prompt-injection filter layer (heuristics + a small classifier prompt on the fast model) and structurally separate untrusted text (delimited, role-tagged, never concatenated into system prompts).
* Privacy: local-first design. Sanitize before any LLM call: mask Aadhaar/PAN/card/OTP/phone patterns and pseudonymise family member names ("FAMILY_1"). Encrypt stored utterance text at rest (Fernet, key from env). Provide data-retention purge job and a "delete everything" endpoint/button.
* Consent: before any recording/transcription feature is used, show a clear DPDP-style consent screen (purpose, what is stored, retention, how to delete). Store the consent record. No audio is stored by default; transcripts only.
* Not legal advice: complaint drafts are drafts for the user to review; the app never files anything itself. Show this clearly.
* Never claim the system catches real criminals. UI copy for demo: "simulation".
* Do not scrape, do not collect real victims' data, do not include real scammer numbers/UPI IDs in the repo or fixtures (use obviously fictional ones).

4. ARCHITECTURE & STACK
Monorepo:

scam-khel/
  LICENSE (MIT)  README.md  ARCHITECTURE.md  DECISIONS.md  DEVLOG.md  PLAN.md
  SECURITY.md  PRIVACY.md  FEEDBACK_DRAFT.md  DEVPOST_DESCRIPTION.md  DEMO_SCRIPT.md
  .env.example  .gitignore  Makefile  docker-compose.yml  .github/workflows/ci.yml
  docs/ (MANUAL_STEPS.md, architecture diagrams as Mermaid, screenshots/)
  backend/  (Python 3.11, FastAPI)
    app/ main.py config.py logging.py
      llm/ client.py router.py prompts/ schemas.py usage.py
      detect/ taxonomy.py rules.py tagger.py risk.py sanitizer.py injection.py
      persona/ persona.py stalling.py decoys.py output_guard.py
      simulator/ scenarios/*.yaml scammer.py runner.py
      evidence/ extractor.py regexes.py
      verify/ tavily_verifier.py
      memory/ db.py models.py repo.py scripts.py retrieval.py learn.py crypto.py
      actions/ telegram.py complaint.py pdf.py blocklist.py alerts.py
      voice/ asr.py tts.py (adapters)
      api/ routes_sessions.py routes_family.py routes_memory.py routes_admin.py ws.py
      guards/ ratelimit.py budget.py demo_mode.py
    tests/ (unit, integration, safety, e2e-smoke)
    evals/ (datasets/, run_eval.py, report.md output)
    scripts/ check_models.py seed_demo.py purge.py
    pyproject.toml  Dockerfile
  frontend/ (Next.js 14 App Router, TypeScript, Tailwind)
    app/ page.tsx live/ simulate/ incidents/ family/ memory/ about/ parent/
    components/ lib/ (ws client, i18n en/hi)
    Dockerfile  playwright tests

Backend: FastAPI, pydantic v2, SQLAlchemy 2 + SQLite (WAL) via aiosqlite (Postgres-ready via env), `openai` Python SDK pointed at Nebius `base_url`, `httpx`, `tavily-python`, `reportlab` (PDF), `cryptography` (Fernet), `slowapi` or custom rate limiter, `structlog`. WebSocket for live sessions. Lint: ruff + mypy (strict where practical). Tests: pytest + pytest-asyncio. Frontend: Next.js + Tailwind, WebSocket client, i18n (English + Hindi), accessible, mobile-first.
5. NEBIUS TOKEN FACTORY + NVIDIA MODELS
Env vars (`.env.example` must list ALL, with comments):

NEBIUS_API_KEY=
NEBIUS_BASE_URL=https://api.tokenfactory.us-central1.nebius.com/v1/   # VERIFY in the Token Factory dashboard; docs show more than one host
MODEL_FAST=      # small Nemotron (e.g., a Nemotron 3 Nano variant) — per-utterance tagging, injection screening
MODEL_MID=       # mid Nemotron (e.g., a Nemotron 3 Super variant) — persona, scammer simulator, orchestration
MODEL_DEEP=      # strongest Nemotron (e.g., a Nemotron 3 Ultra variant) — final analysis + complaint
TAVILY_API_KEY=
TELEGRAM_BOT_TOKEN=
FERNET_KEY=
DEMO_MODE=false  DAILY_TOKEN_BUDGET=  PER_IP_SESSIONS_PER_HOUR=  ...

Do not trust any model ID I (or this prompt) give from memory. Build `scripts/check_models.py` that: calls `GET /v1/models`, prints available NVIDIA models, validates that MODEL_FAST/MID/DEEP exist, runs a 1-token smoke test on each, detects whether native tool/function calling and JSON mode / structured output work, measures latency, and writes `docs/model_report.md`. Choose the architecture's structured-output strategy from that result: use native tool calling if it works reliably; otherwise a strict JSON-schema prompt protocol with pydantic validation + up to 2 repair retries. `llm/client.py` must provide: async client, timeouts, retries with jitter on 429/5xx, per-tier model routing, streaming, strip any reasoning/`<think>` blocks before parsing, token usage accounting per tier (persisted; exposed at `/api/admin/usage` and shown in README as the cost-tiering proof), and a request-ID in every log line. Respect each model card's reasoning on/off switch if one exists (record finding in DEVLOG).
6. FEATURE SPEC
6.1 Tactic taxonomy & detection (`detect/`)
Taxonomy (each with id, description, severity, EN/HI/Hinglish keyword rules): `authority_impersonation`, `fear_arrest_threat`, `isolation_secrecy` ("don't tell anyone"), `stay_on_camera_digital_arrest`, `urgency_deadline`, `fake_case_or_badge_id`, `document_demand` (Aadhaar/PAN/bank), `safe_account_transfer`, `verification_fee_or_deposit`, `remote_access_app_request`, `otp_request`, `link_or_apk_push`, `family_member_implicated`. Hybrid detector: deterministic multilingual rule engine + `MODEL_FAST` tagger returning structured JSON per utterance `{tactics:[{id,confidence,evidence_span}], stage, language}`. Risk engine: score 0–100 combining tactic severity, co-occurrence, stage progression (contact → accusation → isolation → verification → payment demand) and money-request presence. Thresholds: `caution ≥40`, `high ≥70`, `critical ≥85`. Must reach `critical` before or at the first explicit payment demand on all scam fixtures. Output a plain-language explanation in the user's language and a "what to do now" list (hang up, don't pay, call 1930, tell family). False positives matter: genuine bank/delivery/police-station calls must stay below `high` (eval it).
6.2 Memory & learning (`memory/`) — the Personal AI core
Persistent store: users, family circle, incidents, utterances (encrypted), tactics timeline, evidence items, scam_scripts library (seed ~15 generic script patterns: tactic sequence + normalised phrase templates, authored by you, no real identifiers), reports, consent records, alert log.

* Before each session: load family profile + retrieve similar past scripts (FTS5 + tactic-sequence similarity; add embeddings only if an embedding model is available on Token Factory — verify via check_models).
* After each session: learn — fingerprint the observed script (tactic sequence + salient normalised phrases), upsert into library with counts, and update recognition priors.
* Visible proof: second run of a similar scenario must show "Recognised pattern from Incident #N — flagged at turn k vs turn m earlier" in the UI and in the eval report. Build this as a first-class metric.

6.3 Honeypot persona (`persona/`)
`MODEL_MID` persona: slow, polite, hard-of-hearing elderly Hinglish speaker (configurable: name, age, language mix, quirks). Stalling library (look for glasses, call the "son", battery low, can't open the app, "say it again slowly", ask for officer's name/ID/office address/callback number/written notice) — chosen by a policy that maximises engaged turns while eliciting identifiers (names, badge/case numbers, phone numbers, UPI IDs, bank names, URLs). Rules: always stay in persona, never reveal AI or detection, never comply with payment/install/click/OTP, use only decoys, pass every output through `output_guard`. Ends when scammer disengages, max turns, or user takes over. Track time wasted (simulated seconds from turn count/typing+TTS durations).
6.4 Scammer simulator (`simulator/`)
Scenario YAMLs (at least 6): digital-arrest-parcel, digital-arrest-money-laundering, fake-customs, fake-police-family-accident, KYC-expiry-bank, courier-drug-package. Each defines stages, goals, pressure escalation, and language. `MODEL_MID` plays the scammer constrained by the scenario state machine; it is explicitly fictional ("National Crime Verification Cell (SIMULATION)"). Autoplay mode (speed control) for demo video + manual mode where the human plays the "victim". Include an adversarial scammer scenario that attempts prompt injection against the honeypot to prove the guard works.
6.5 Evidence extraction (`evidence/`)
Structured extraction (regex + `MODEL_DEEP`/`MODEL_MID` JSON schema, cross-checked): phone numbers (+91 / 10-digit), UPI IDs, account/IFSC patterns, URLs/APK names, claimed agency, officer names, badge/case IDs, amounts, deadlines, script stage. Deduplicate, attach confidence + source utterance reference. Live evidence panel via WebSocket.
6.6 Tavily verification (`verify/`)
`tavily-python` runtime calls to (a) check the claimed officer/agency/case-ID claims against official advisories (restrict `include_domains` to official/government sources such as cybercrime.gov.in, pib.gov.in, mha.gov.in, rbi.org.in, plus reputable news — verify param names in Tavily docs), (b) fetch the current official advisory text to ground the "what to do" copy, (c) best-effort search for reports of the extracted number/UPI ID. Cache results; handle quota errors gracefully; clearly label "no public reports found" ≠ "safe". Show Tavily results with sources in the UI.
6.7 Actions (`actions/`) — the "real action" proof

* Family alert via Telegram Bot API (plain `httpx`): family members join with a `/start <code>`; alert includes risk level, tactics, one-line plain-language summary, "call your parent now" guidance, link to incident. Rate-limit and dedupe alerts; escalate `critical` once.
* Complaint draft (PDF + Markdown): complainant fields left for the user to fill, incident timeline, modus operandi summary, identifier table, transcript excerpts (redacted option), requested actions, annexure list, prominent note: "DRAFT — review and file at cybercrime.gov.in; if money was transferred, call 1930 immediately." Never auto-submit.
* Panic flow ("I already sent money"): immediate checklist (call 1930, note transaction details, contact bank, screenshot evidence), pre-fills a transaction-details form, generates the 1930 call script + complaint draft.
* Blocklist export: CSV/JSON of extracted identifiers (for the user to share with their bank/telecom).

6.8 Voice (Phase 7, optional but valuable)
Adapters: `ASR` — NVIDIA Parakeet/Nemotron-speech (local NeMo or NIM-style endpoint) when available, fallback browser Web Speech API (hi-IN/en-IN). `TTS` — NVIDIA Magpie TTS multilingual (Hindi) when available, fallback browser `speechSynthesis`. Interface-based so text mode always works. Record in DECISIONS.md which path is actually used in the demo; be honest in README that the fallback is not NVIDIA (the NVIDIA-model requirement is satisfied by Nemotron on Token Factory).
7. DATA MODEL (SQLAlchemy)
`User`, `FamilyMember(telegram_chat_id, role)`, `ConsentRecord`, `Session(mode, scenario, language, started_at, ended_at, risk_peak, time_wasted_s)`, `Utterance(speaker, text_enc, ts, tactics_json, risk_after)`, `EvidenceItem(type, value, confidence, utterance_id)`, `Incident(session_id, summary, recognised_script_id, detect_turn)`, `ScamScript(id, name, tactic_sequence, phrases, seen_count, first_seen, last_seen)`, `Report(incident_id, pdf_path, md)`, `AlertLog`, `UsageLog(model_tier, prompt_tokens, completion_tokens, latency_ms)`. Alembic migrations.
8. API
`POST /api/sessions` (mode, scenario, language, consent=true) · `WS /ws/sessions/{id}` (client: `utterance`, `audio_chunk`, `control`; server events: `transcript`, `tactics`, `risk`, `persona_token`, `persona_reply`, `evidence`, `verification`, `memory_hit`, `alert_sent`, `summary`, `budget_notice`) · `POST /api/sessions/{id}/end` · `GET /api/sessions/{id}/complaint.pdf|md` · `POST /api/analyze` (one-shot Shield) · `POST /api/panic` · `GET/POST /api/family`, `POST /api/family/test-alert` · `GET /api/incidents`, `GET /api/incidents/{id}` · `GET /api/memory/scripts` · `GET /api/blocklist.csv|json` · `DELETE /api/me/data` · `GET /healthz` · `GET /api/models/status` · `GET /api/admin/usage` (token-protected). Validate everything with pydantic; cap request sizes; CORS locked to the frontend origin.
9. FRONTEND
Design: dark, calm, high-contrast, trust-forward; Indian context; big type; Hindi/English toggle; WCAG AA; mobile-first. Pages:

* `/` landing: 20-second explainer, consent, mode picker.
* `/simulate`: scenario picker + autoplay/manual; split view: live conversation | risk meter + tactic timeline | evidence panel | Tavily verification | time-wasted counter | memory-hit banner.
* `/live`: Shield mode console (paste/speak/stream).
* `/parent`: elderly-friendly view; giant buttons; "I already sent money" red flow.
* `/incidents`, `/incidents/[id]`: replay, evidence, complaint download.
* `/family`: circle management + test alert. `/memory`: known + learned scripts with counts. `/about`: architecture diagram, which Nemotron tier does what, privacy promises, honest limitations. Every simulator screen must visibly carry "SIMULATION" labelling. Include empty/error/loading states and a "budget exhausted → replay mode" state.

10. SECURITY & PRIVACY CHECKLIST (implement + test)
Secrets via env only · gitleaks in CI · input size limits · rate limits per IP/session · prompt-injection filter + structural separation · output guard · PII sanitizer before LLM calls · Fernet at-rest encryption · retention purge (`scripts/purge.py`, cron-able) · delete-my-data · structured logs with PII redaction · dependency audit (pip-audit, npm audit) · security headers · no third-party trackers · `PRIVACY.md` and `SECURITY.md` written honestly (DPDP-style consent, minimisation, retention, limits).
11. TESTING & EVALS (this is what wins "Technological Implementation" and "Impact")

* Unit tests: rules, risk engine, sanitizer, output guard, evidence regexes, decoys, PDF generation, Telegram client (mocked), memory learn/retrieve.
* Safety tests: persona never leaks real-looking data under 30+ adversarial prompts; payment/OTP/install/click requests are always refused in persona; injection attempts neutralised; sanitizer masks all patterns.
* Integration tests with a recorded/mocked Token Factory + a live smoke test (skipped without key) hitting the real API.
* Eval harness (`make eval`): author ≥ 40 synthetic labelled dialogues in English/Hindi/Hinglish — ≥ 25 scam (across scenarios), ≥ 15 legitimate (genuine bank alerts, courier delivery, real police-station follow-up, family chats). Metrics: precision/recall/F1 at `high` threshold, turns-to-detect, false-positive rate on legit set, honeypot engaged turns / time wasted, identifiers extracted per session, memory benefit (turns-to-detect on 2nd vs 1st exposure), persona leakage rate (target 0), p50/p95 latency per tier, tokens/cost per session by tier. Emit `evals/report.md` + JSON, and embed the headline table in README.
* Frontend: Playwright e2e smoke (landing → consent → run simulation → see risk climb → download complaint PDF).
* CI: ruff, mypy, pytest, eval-lite (offline), frontend lint/build/test, gitleaks.

12. DEVOPS, DEMO MODE, DEPLOY

* `docker-compose.yml` for one-command local run; `Makefile` targets: `setup`, `dev`, `test`, `eval`, `seed`, `demo`, `lint`, `check-models`, `purge`.
* DEMO_MODE (must keep the public demo alive and free until Dec 15): global daily token budget, per-IP/session limits, max turns per session, request caps, graceful degradation to pre-recorded replay sessions (generated from real runs, clearly labelled "replay") when budget is exhausted, `/healthz` and budget status exposed. Never fail with a blank screen.
* Deploy: frontend on Vercel (or equivalent); backend as a container on a low-cost host (Render/Fly/Railway) with persistent volume for SQLite. Document exact steps in README. If Nebius Serverless Endpoints/Jobs are used for anything (e.g., eval batch runs), document it — optional, not required.
* Provide `make demo` that seeds the DB with two prior incidents so the memory-hit moment is reproducible on camera.

13. DOCUMENTATION DELIVERABLES

* `README.md` (judge-facing): hero GIF/screenshots placeholder list, problem (with the context facts above), what it does, "How it uses Nebius Token Factory + NVIDIA Nemotron" section (tier table: which model does what, why; token-usage table), "Where Tavily is used", architecture diagram (Mermaid), quickstart (< 10 min), env vars, eval results table, safety & privacy, honest limitations (no real-call interception; simulation-only honeypot; drafts not filings; Tavily best-effort), roadmap, license.
* `ARCHITECTURE.md` with Mermaid sequence + component diagrams.
* `DEVPOST_DESCRIPTION.md`: what/why/how, Built With list (Nebius Token Factory, NVIDIA Nemotron, Tavily, FastAPI, Next.js, …), challenges, what's next.
* `DEMO_SCRIPT.md`: a second-by-second 3:00 script — problem (0:00–0:20) → Shield catches live scam transcript (to 0:50) → honeypot takes over simulated scammer, evidence panel fills, time-wasted counter climbs (to 1:40) → Tavily verification + memory-hit on second run (to 2:10) → family Telegram alert + complaint PDF + panic flow (to 2:40) → closing with explicit on-screen + spoken callouts of Nebius Token Factory and NVIDIA Nemotron (to 3:00). Include shot list, narration text, required screen states, and the seed/reset commands.
* `FEEDBACK_DRAFT.md`: pre-filled from `DEVLOG.md` — what I used each tool for, what worked, what needs work, onboarding time zero-to-hello-world, would-I-build-again — specific, naming the tool each time.
* `docs/MANUAL_STEPS.md`: everything only I can do (create accounts/keys, claim credits with code NEBIUS-DEVPOST-GLOBAL26, join Nebius Builders Program, create Telegram bot via BotFather, record video on YouTube, submit on Devpost, confirm repo license shows in About).

14. PHASES & ACCEPTANCE CRITERIA
P0 Foundations — repo scaffold, config, CI, LICENSE, `.env.example`, secret scanning, `llm/client.py` (retry, streaming, think-strip, usage accounting), `scripts/check_models.py` + `docs/model_report.md`. Accept: `make test` green; check_models validates the three tiers against the live API (or fails with a clear message listing MANUAL_STEPS). P1 Detection core (text) — taxonomy, rules, tagger, risk engine, sanitizer, injection filter, first 20 dialogue fixtures. Accept: unit tests; scam fixtures reach `critical` by first payment demand; legit fixtures stay < `high`. P2 Memory & learning — DB, migrations, encryption, script library seed, retrieval, learn step, memory-hit event. Accept: integration test proves 2nd exposure is flagged earlier. P3 Persona + simulator + orchestrator — persona, stalling policy, decoys, output guard, 6 scenarios + adversarial scenario, runner, orchestration loop (detector → risk → persona/alerts/evidence). Accept: autoplay run completes; 0 leakage in safety suite; adversarial scenario neutralised. P4 Evidence + Tavily + Complaint — extractor, verifier with caching, complaint PDF/MD, blocklist export. Accept: sample session yields ≥ 5 identifier types and a valid PDF. P5 Actions — Telegram alerts (dedupe/rate-limit), panic flow, alert log. Accept: mocked-Telegram tests; live test-alert endpoint works with real bot token. P6 API + WebSocket + Frontend — all endpoints, all pages, i18n, SIMULATION labelling, error/empty/budget states, Playwright smoke. Accept: full flow runs in browser end-to-end. P7 Voice (optional) — ASR/TTS adapters + UI mic/speaker controls. Accept: text mode unaffected; voice works on at least the fallback path; document the NVIDIA path status honestly. P8 Hardening & Ship — eval suite + report, DEMO_MODE + replay fallback, Dockerfiles/compose, deploy docs, README/ARCHITECTURE/DEVPOST/DEMO_SCRIPT/FEEDBACK_DRAFT/PRIVACY/SECURITY, `make demo` seeding, final audit. Accept: Section 15.
15. DEFINITION OF DONE (verify and print a checklist report at the end)

* [ ] `make setup && make test && make eval` pass from a clean clone.
* [ ] `docker compose up` serves the full app locally; `make demo` reproduces the memory-hit moment.
* [ ] Live Token Factory calls verified with all three tiers; `docs/model_report.md` committed.
* [ ] Tavily runtime call visible in the UI and in logs.
* [ ] Telegram alert delivered in a real test; complaint PDF opens and reads correctly.
* [ ] Safety suite: persona leakage = 0; injection tests pass; no secrets in git history (`gitleaks` clean).
* [ ] Eval report with real numbers embedded in README (no invented figures).
* [ ] DEMO_MODE tested by forcing budget exhaustion → replay mode works, no blank screens.
* [ ] LICENSE (MIT) at root; README clearly names Nebius Token Factory + NVIDIA Nemotron + Tavily with the tier table.
* [ ] No third-party logos/trademarks or copyrighted media anywhere in the app or demo assets; every simulator screen says SIMULATION.
* [ ] DEMO_SCRIPT.md timed to ≤ 3:00 and rehearsed against the actual UI; FEEDBACK_DRAFT.md filled from DEVLOG.
* [ ] A final "What I could not verify / what you must do manually" list.

START NOW: read the spec once more, write PLAN.md and DECISIONS.md, then begin Phase P0. Report concise progress at the end of each phase (what passed, what's next, any blocker).
```

**Response:** PLAN.md and DECISIONS.md written; P0 delivered (commit `e8d036c`). Because the home directory was already a git repo, a fresh repo was created inside the project folder.

---

## Conversation log (all later prompts, verbatim)

| # | You said | What was done | Key commits |
|---|---|---|---|
| 2 | *"how to add nebius key idk tell me step wise"* | Step-by-step guide: create Nebius account, claim credits, create key, copy `.env.example` to `.env`, set `NEBIUS_API_KEY` and base URL, run `check_models.py`, pick the three Nemotron IDs. (Never paste the key in chat.) | - |
| 3 | *"skip this phase for now and continue with phase 2"* | Skipped the live-key step and built **P2 memory & learning** against synthetic tactic sequences: SQLAlchemy models, WAL SQLite, FTS5 index, Alembic migration 0001, Fernet encryption, consent, retention purge, delete-all, 15 seed scripts, recognition with learned priors. Test proves a repeat is flagged earlier. | `af89c36` |
| 4 | *"Build P1 (detection core) next, since memory needs the detector to produce real tactic sequences."* (chosen from a button) | **P1**: 13-tactic EN/Hindi/Hinglish rules with negation guard, PII sanitizer, prompt-injection filter, hybrid tagger, monotonic risk engine, 22 labelled dialogues (all 14 scams critical by payment demand, all 8 legit below high). | `82c56a8` |
| 5 | *"continue to do all the phases pls without asking my permission"* | Autonomous build of **P3 to P8**: persona + output guard + simulator + orchestrator (P3), evidence + Tavily + complaint PDF + blocklist (P4), Telegram alerts + panic flow (P5), FastAPI + WebSocket + guards + demo-mode replay (P6 backend), Next.js frontend with HIG-derived design and EN/HI (P6 frontend), voice adapters (P7), evals + Docker + docs + final audit (P8). | `5ef4f1f` .. `0eb4c4e` |
| 6 | *"I'll add keys later. Summarise exactly what I must do manually."* | Wrote the manual checklist (accounts/keys, live verification, Docker, deploy, video, Devpost). Also in `docs/MANUAL_STEPS.md`. | - |
| 7 | *"make a professional github repo and pls make this as professional as possible pls"* | Community files (CONTRIBUTING, CODE_OF_CONDUCT, SUPPORT, CHANGELOG), issue/PR templates, CODEOWNERS, Dependabot, CodeQL, hardened CI, `.gitattributes`/`.editorconfig`, README with badges and real screenshots; created the GitHub repo. Fixed a bug (explanations followed the caller's language, not the UI's). | `da77c8b` |
| 8 | *"I ran gh auth refresh with the workflow scope. Push to origin main, set repo topics, and verify CI starts."* | Pushed, set 12 topics, enabled Discussions; first gitleaks failure traced to the first-push commit range (not a leak). | - |
| 9 | *"can u make this repo public if it is private pls"* | Made the repo public; confirmed MIT licence detected; enabled private vulnerability reporting. | - |
| 10 | *"can u make the UI more professional and easy to use and nice pls"* | UI polish: persistent "Call 1930" bar, landing hero + sample analysis, gauge risk meter + stage stepper, example buttons, chat-style transcript, skeleton loaders, app icon, calmer layouts. | `33c9b11` |
| 11 | *"can u show me the UI pls"* | Seeded the demo DB, started backend + frontend, opened the app in the preview pane. | - |
| 12 | *"is there a way it can like intercept real calls when the person clicks on a widget or something and can file the report as well"* | Explained limits: a web widget cannot intercept call audio; OS restrictions on iOS/Android; feasible alternatives (Listen mode, Chrome extension, Android call-screening app). Declined auto-filing (portal needs login/OTP/captcha); proposed an assistive Report page instead. | - |
| 13 | *"build both and also make the UI more better and not just dark mode pls"* | Built **Listen mode** (continuous browser speech-to-text feeding Shield, consent sheet) and the **Report assistant** (`/report` + `report-fields` API, copy buttons, step checklist, never submits). Added a **light (default) / auto / dark theme** with no-flash init, landing features + FAQ. | `7735111` |
| 14 | *"there are some pull requests pls check and merge them"* | Reviewed 16 Dependabot PRs. Merged the green ones (Actions bumps, autoprefixer, postcss, ESLint 10, `@types/node` patch); applied Tailwind/TypeScript minor bumps directly; closed TypeScript 7, Tailwind 4, Node 25, Python 3.14 and `@types/node` 26 with explanations; tightened `dependabot.yml`. | `bf773ef` .. `42cb94f` |
| 15 | *"MAKE ME A DOC SAYING AND SHOWING ALL THE PROMPTS AND THE WORK DONE ON THIS PROJECT AND ALSO THE REMAINING PARTS AND IMPROVEMENTS TO BE DONE AS ILL BE GIVING THE WORK TO MY TEAM TO FINISH AND ADD MORE ON THIS PROJ PLS HELP ME"* | This document and `HANDOVER.md`. While gathering facts, found that the *deep* Nemotron tier was documented but never called; wired it (final analysis + complaint narrative) and corrected the tool-calling docs. | `72b83c1` |
| 16 | *"check out the handover.md and prompts.md in the docs folder and pls complete the remaining . This is a group project. ensure nothing goes wrong and do as per instructions"* | Executed remaining engineering backlog tasks: security & guard hardening (XFF proxy awareness P1-04, budget persistence P1-03, P0-10); detection recall improvements to 100% on all 26 scams without hurting FP rate (P1-07); native tool-calling structured mode with automatic JSON fallback (P1-01); user feedback loop with DB migration 0003, API, and UI (P1-08); server-side in-memory ASR streaming endpoint (P1-10); Telegram webhook registration script (P0-06); Docker entrypoint with automated Alembic migrations and compose healthcheck (P0-07). All 446 tests, mypy strict, ruff, and Next.js production builds verified green. | `8673776` .. `d68866f` |

### Notes on the "button" prompts
Some messages (e.g. #4, #8) were sent by clicking suggested-reply buttons in the app; their text is quoted exactly as sent.

---

## Reusable prompt templates for your team

Use these with Claude Code (or any coding assistant) after cloning the repo. Always start by pointing the assistant at the handover doc.

**Start-of-session context**
```text
Read docs/HANDOVER.md, DECISIONS.md and docs/FINAL_AUDIT.md first. Follow CONTRIBUTING.md.
Task: <one backlog item ID from HANDOVER.md §6, e.g. P1-03>.
Constraints: synthetic data only; fictional agencies keep "(SIMULATION)"; never contact real
scammers; do not weaken the output guard or sanitizer; add tests; keep ruff/mypy/eslint/tsc green.
Do not tune detection rules to the held-out eval set without saying so in the PR.
```

**Adding a scam tactic or language**
```text
Add tactic <id> (severity N) to backend/app/detect/taxonomy.py with EN/Hindi/Hinglish rules in
rules.py (include a negation case, e.g. "never share ..."), add labels in frontend/lib/labels.ts,
add 3 scam + 2 legit dialogues to backend/evals/datasets/dialogues_eval.yaml, run `make eval`
and report precision/recall before and after.
```

**New scenario for the simulator**
```text
Add backend/app/simulator/scenarios/<id>.yaml following digital-arrest-parcel.yaml: fictional
agency labelled (SIMULATION), fictional identifiers (90000 00xxx phones, @examplebank UPI),
stages contact -> accusation -> isolation -> verification -> payment. Add it to the autoplay
test parametrisation and confirm persona leakage stays 0.
```

**Live-service verification**
```text
With NEBIUS_API_KEY and MODEL_* set in .env: run `make check-models`, commit docs/model_report.md,
run `make eval-live`, commit backend/evals/report.md, then re-record replays with
`python backend/scripts/make_replays.py --live`. Report latency per tier and tokens per session.
```

**UI change**
```text
Follow Apple HIG principles translated to web (semantic colour tokens in frontend/app/globals.css,
44px targets, visible focus, prefers-reduced-motion, light/auto/dark, EN + HI strings in
frontend/lib/i18n.tsx and i18n-extra.ts). Add or update a Playwright test in frontend/e2e and
regenerate screenshots with `SCREENSHOTS=1 npx playwright test screenshots`.
```
