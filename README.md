<div align="center">

# 🛡️ SCAM-KHEL

**A private, always-on family shield against Indian "digital arrest" scams.**

Detect coercion in real time · waste scammers' time with a simulated decoy · alert the family · draft the complaint.

[![CI](https://github.com/Kaushik2210/scam-khel/actions/workflows/ci.yml/badge.svg)](https://github.com/Kaushik2210/scam-khel/actions/workflows/ci.yml)
[![CodeQL](https://github.com/Kaushik2210/scam-khel/actions/workflows/codeql.yml/badge.svg)](https://github.com/Kaushik2210/scam-khel/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)
![Next.js](https://img.shields.io/badge/Next.js-16-black)
![LLM](https://img.shields.io/badge/LLM-NVIDIA%20Nemotron%20on%20Nebius%20Token%20Factory-76b900)

Built for the **Nebius × NVIDIA Global AI Hackathon** · Personal AI track

<img src="docs/screenshots/04-memory-hit.png" alt="Simulation view: transcript, risk meter at high, memory-hit banner, evidence, Tavily checks and tactic timeline" width="860">

</div>

> **Simulation only.** The honeypot talks to a built-in, fictional scammer simulator (every agency is labelled `(SIMULATION)`). SCAM-KHEL does not intercept real calls, never contacts real scammers, and never files anything for you. Complaints are drafts for you to review.

**Contents:** [Problem](#the-problem) · [What it does](#what-it-does) · [Screenshots](#screenshots) · [Nebius + NVIDIA + Tavily](#how-it-uses-nebius-token-factory--nvidia-nemotron) · [Architecture](#architecture) · [Quickstart](#quickstart-10-min) · [Evaluation](#evaluation-results) · [Demo mode](#demo_mode-keeps-the-public-demo-alive-until-dec-15) · [Safety & privacy](#safety-and-privacy-summary) · [Limitations](#honest-limitations) · [Repo layout](#repository-layout) · [Contributing](#contributing)

## The problem

Fraudsters impersonate police, CBI, ED or customs, claim you or a family member is implicated in a crime, keep you "visible" on a video call, tell you not to tell anyone, and demand a transfer to a "safe / verification account". Indian authorities state that police, CBI, ED and courts do not arrest people over video calls. If money is lost, call helpline **1930** and report at **https://cybercrime.gov.in**.

## What it does

| Mode | What happens |
|---|---|
| **Shield** (detect) | Paste, speak or stream what a caller said. 13 coercion tactics are tagged live (English / Hindi / Hinglish); a 0-100 risk score climbs through `caution ≥40`, `high ≥70`, `critical ≥85`, with a plain-language explanation and a "what to do now" list. |
| **Honeypot** (bait) | A decoy "confused grandmother" persona stalls a **simulated** scammer, asks for names, IDs, numbers and payment details, and the evidence panel fills while a time-wasted counter climbs. |
| **Listen mode** | Put a real call on speaker; the browser turns speech into text (hi-IN / en-IN) and Shield scores it live, with a consent prompt first. Needs a browser with speech recognition (Chrome / Edge). SCAM-KHEL stores no audio, but the browser's speech service may process it. |
| **Report assistant** | Step-by-step guide for cybercrime.gov.in with a copy button for every field of the draft. The portal needs your own login, OTP and captcha, so **SCAM-KHEL never submits anything for you**. |
| **Parent view** | Very large buttons: "Is this a scam?" and a red **"I already sent money"** flow (1930 checklist, call script, pre-filled transaction form, complaint draft). |
| **Memory** | Scam scripts are fingerprinted and remembered. A repeat run shows *"Recognised pattern from Incident #N, flagged at turn k vs turn m earlier"* and is treated as high risk immediately. |
| **Actions** | Telegram family alert, complaint draft (PDF + Markdown) for cybercrime.gov.in, blocklist export (CSV/JSON). |

## Screenshots

| | |
|---|---|
| ![Landing](docs/screenshots/01-landing.png) **Landing** | ![Consent](docs/screenshots/02-consent.png) **DPDP-style consent** |
| ![Simulation](docs/screenshots/03-simulate.png) **Honeypot simulation** | ![Shield](docs/screenshots/05-shield.png) **Shield: pasted call at critical** |
| ![Parent view](docs/screenshots/06-parent-mobile.png) **Parent view (mobile)** | ![Dark theme](docs/screenshots/09-simulate-dark.png) **Dark theme (Light / Auto / Dark toggle)** |
| ![Report assistant](docs/screenshots/07-report-assistant.png) **Report assistant: copy-ready fields** | ![Listen mode](docs/screenshots/08-listen-mode.png) **Listen mode** |

All screenshots are captured from the running app by `frontend/e2e/screenshots.spec.ts` (offline mode: no API keys were used). The UI defaults to a light theme and also has dark and auto.

## How it uses Nebius Token Factory + NVIDIA Nemotron

All runtime LLM calls go to **Nebius Token Factory** (OpenAI-compatible API) and use **NVIDIA Nemotron** models in three cost tiers. Model IDs are never hard-coded: set `MODEL_FAST`, `MODEL_MID`, `MODEL_DEEP`, and run `make check-models` to list the Nemotron models your account can use, smoke-test each tier, probe tool-calling / JSON support, and write `docs/model_report.md`.

| Tier | Env var | Used for | Why this tier |
|---|---|---|---|
| **Fast** (small Nemotron) | `MODEL_FAST` | Per-utterance tactic tagging; prompt-injection classifier on ambiguous text | Runs on every message, so it must be cheap and quick |
| **Mid** (mid-size Nemotron) | `MODEL_MID` | Honeypot persona, scammer simulator, semantic evidence cross-check | Needs fluent, in-character Hinglish |
| **Deep** (largest Nemotron) | `MODEL_DEEP` | Final analysis and complaint narrative | Runs once per incident; quality matters more than latency |

`backend/app/llm/client.py` provides the async client, retries with jitter on 429/5xx, per-tier routing, streaming, `<think>` stripping, a JSON-schema protocol with pydantic validation and up to two repair retries, a request ID in every log line, and **per-tier token accounting** exposed at `GET /api/admin/usage` (the cost-tiering proof).

**Token usage by tier:** produced by `make eval-live` (needs a Token Factory key) and by `/api/admin/usage`. The repository ships the *offline* eval run, which makes zero LLM calls, so there are no token figures to quote yet; none are invented here. See [`backend/evals/report.md`](backend/evals/report.md).

### Where Tavily is used

`backend/app/verify/tavily_verifier.py` makes runtime calls (visible in the UI under "Public-source checks" and in the logs) to (a) fetch the current official advisory text, restricted to `cybercrime.gov.in`, `pib.gov.in`, `mha.gov.in`, `rbi.org.in` and similar, (b) check the claimed agency against official sources, and (c) best-effort search for public reports of an extracted phone number or UPI ID. Results are cached, quota errors degrade gracefully, and **"no public reports found" is always labelled as *not* meaning safe**.

## Architecture

```mermaid
flowchart LR
  U[Call text / speech] --> S[PII sanitizer + injection filter]
  S --> T["Tagger: rules + Nemotron fast"]
  T --> R[Risk engine + memory prior]
  R --> UI[Live UI over WebSocket]
  R -->|high/critical| A[Telegram family alert]
  T --> E[Evidence extractor]
  E --> V[Tavily verification]
  R --> P["Honeypot persona (Nemotron mid) + output guard"]
  P --> SIM[Scammer simulator]
  SIM --> T
  R --> M[(Memory: SQLite, Fernet, FTS5)]
  E --> C[Complaint PDF/MD + blocklist]
```

More diagrams in [ARCHITECTURE.md](ARCHITECTURE.md); decisions and trade-offs in [DECISIONS.md](DECISIONS.md).

## Quickstart (< 10 min)

Prerequisites: Python 3.11+, Node 20+. A Nebius Token Factory key is optional: without it the app runs in clearly flagged **offline mode** (rules + scripted fallbacks).

```bash
git clone https://github.com/Kaushik2210/scam-khel.git && cd scam-khel
cp .env.example .env            # fill NEBIUS_API_KEY and MODEL_* (see docs/MANUAL_STEPS.md)
make setup                      # backend deps
cd frontend && npm install && cd ..
make check-models               # lists Nemotron models, validates tiers, writes docs/model_report.md
make test                       # backend tests
make eval                       # offline eval -> backend/evals/report.md + table below
make demo                       # seeds two prior incidents so the memory-hit moment is reproducible
make dev                        # API on :8000   (second terminal: cd frontend && npm run dev)
```

Start the frontend with `NEXT_PUBLIC_ALLOW_CLIENT_PARAM=1` (demo only, see `frontend/.env.example`), then open <http://localhost:3000/?client=demo-client-0001> to see the seeded incidents. Or: `docker compose up --build`.

**Deploy:** frontend on Vercel (`NEXT_PUBLIC_API_URL` = your API URL); backend container (`backend/Dockerfile`) on Render / Fly / Railway with a persistent volume at `/data`, `DEMO_MODE=true`, `FRONTEND_ORIGIN` = the Vercel URL, `ADMIN_TOKEN` and `FERNET_KEY` set, and `TRUSTED_PROXIES` set to the address range of the host's proxy (without it every visitor shares the proxy's address and the per-IP limits apply to everyone together). Details in [docs/MANUAL_STEPS.md](docs/MANUAL_STEPS.md).

### Environment variables

Every variable is documented in [`.env.example`](.env.example): Nebius, the three model tiers, Tavily, Telegram, Fernet key, retention, `DEMO_MODE`, `DAILY_TOKEN_BUDGET`, per-IP limits, optional ASR/TTS endpoints.

## Evaluation results

Measured by `make eval` (offline, deterministic), never hand-written. Full report: [backend/evals/report.md](backend/evals/report.md).

<!-- EVAL:START -->
| Metric | Result |
|---|---|
| Eval set | 43 dialogues (26 scam / 17 legit; EN, Hindi, Hinglish) |
| Precision / recall / F1 @ high (≥70), all | 1.0 / 1.0 / 1.0 |
| Same, held-out set only (21) | 1.0 / 1.0 / 1.0 |
| False-positive rate on legit (all / held-out) | 0.0 / 0.0 |
| Mean scammer turns to reach high | 2.15 |
| Critical by first payment demand | 1.0 |
| Honeypot engaged turns / time wasted (mean, 7 scenarios) | 10.1 / 776s |
| Identifier types extracted per session (mean) | 6.7 |
| Persona leakage rate (guard violations per persona turn) | 0.0000 |
| Memory benefit: turns saved on 2nd exposure (mean) | 0.71 |
| Run mode | live (Nebius Token Factory + Nemotron) |
<!-- EVAL:END -->

Read the numbers honestly: the rules-only detector is weakest on paraphrase, and the *tuned* set is optimistic. One held-out false positive (a public scam-awareness advisory) was fixed after it was observed, so the held-out figures are post-fix. `make eval-live` measures the Nemotron-assisted pipeline once a key is configured.

## DEMO_MODE (keeps the public demo alive until Dec 15)

`DEMO_MODE=true` enforces a global daily token budget, per-IP session limits, a max-turns cap and request-size caps. When the budget is exhausted, live sessions degrade to **pre-recorded replays, clearly labelled "replay"**, Shield keeps working on rules alone (zero tokens), and `/healthz` exposes the budget. There is never a blank screen. Tested by forcing exhaustion (`backend/tests/test_api.py`).

## Safety and privacy (summary)

- The persona only ever uses a fixed fictional decoy identity. An **output guard** blocks and rewrites anything resembling Aadhaar, PAN, card numbers, OTPs, real phone numbers or non-decoy UPI IDs, and any agreement to pay / install / click. Tested against 37 hostile outputs and a 220-case obedient-model matrix: leakage 0.
- Scammer text is untrusted: heuristics + a classifier prompt, structural delimiting, never concatenated into system prompts.
- Personal numbers are masked and family names pseudonymised before any LLM call; transcripts are encrypted at rest (Fernet); 30-day retention purge; "delete everything" endpoint and button; DPDP-style consent screen with a stored consent record; no audio stored.
- See [PRIVACY.md](PRIVACY.md) and [SECURITY.md](SECURITY.md).

## Honest limitations

- No real-call interception. The honeypot is simulation-only; real telephony is future work and intentionally absent.
- Complaints are drafts. You review and file them yourself.
- Detection can be wrong; treat it as a second opinion. Tavily results are best-effort.
- Voice uses the browser's Web Speech API by default, which is **not** an NVIDIA model. NVIDIA ASR/TTS adapters exist but are unverified; the NVIDIA-model requirement is met by Nemotron on Token Factory.
- Live Token Factory, Tavily and Telegram paths are implemented and unit-tested against mocks; they have not been exercised against the real services (no keys were available while building). See [docs/FINAL_AUDIT.md](docs/FINAL_AUDIT.md).

## Repository layout

```
backend/            FastAPI app (Python 3.11+)
  app/llm/          Token Factory client, tier routing, usage accounting
  app/detect/       rules, sanitizer, injection filter, tagger, risk engine
  app/persona/      decoy persona, stalling policy, output guard
  app/simulator/    fictional scenarios + scammer state machine
  app/memory/       SQLAlchemy models, Fernet, FTS5, learning, retention
  app/evidence/     identifier extraction     app/verify/   Tavily
  app/actions/      Telegram, complaint PDF/MD, panic flow, blocklist
  app/api/          REST + WebSocket routes   app/guards/   rate limit, budget, replay
  evals/            datasets, run_eval.py, report.md
  tests/            400+ tests (unit, safety, API, eval-lite)
frontend/           Next.js 16 / React 19 / Tailwind (EN + HI), Playwright e2e
docs/               model report, manual steps, final audit, screenshots
```

## Contributing

Taking over the project? Start with [docs/HANDOVER.md](docs/HANDOVER.md) (status, backlog, gotchas) and [docs/PROMPTS.md](docs/PROMPTS.md). Then read [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md). Use synthetic data only. Security issues: [SECURITY.md](SECURITY.md). History: [CHANGELOG.md](CHANGELOG.md).

## Roadmap

Real bait-line telephony behind a consent-gated feature flag (disabled, future work), on-device ASR, more regional languages, bank/telecom blocklist integrations, embeddings-based script retrieval when available on Token Factory.

## License

[MIT](LICENSE) © 2026 Kaushik
