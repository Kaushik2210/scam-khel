# Decisions

| # | Decision | Reason |
|---|---|---|
| 1 | New git repo inside project dir (`git init -b main`) | The home directory is already a git repo; committing there would pollute it and risk leaking dotfiles. |
| 2 | Python `>=3.11` (dev machine has 3.13) | Spec says 3.11; nothing requires <3.13. CI runs 3.11 and 3.12. |
| 3 | `openai` SDK (AsyncOpenAI) pointed at Nebius `base_url` | OpenAI-compatible API; the SDK is only a transport, no OpenAI endpoint is ever called. |
| 4 | Default structured-output strategy = JSON-schema prompt + pydantic validation + ≤2 repair retries | Safe default until `check_models.py` proves native tool calling is reliable; switch via `STRUCTURED_MODE` env. |
| 5 | Model IDs only from env (`MODEL_FAST/MID/DEEP`) | Spec; IDs from memory are untrustworthy. |
| 6 | Usage accounting persisted to SQLite `usage_log` via a pluggable sink; in P0 an in-memory + JSONL sink | DB layer lands in P2; sink interface avoids rework. |
| 7 | `--offline` mock adapter only in tests / flagged dev mode (`LLM_OFFLINE=1`) | Spec rule 4. |
| 8 | Secret scanning: gitleaks in CI + `pre-commit` config | gitleaks not installed locally; local check done with a regex scan script until installed. |
| 9 | Structured output default stays JSON-prompt + pydantic + 2 repairs | No key => tool-calling reliability unknown; `check_models.py` recommends a mode. |
| 10 | Rules run on raw text locally; LLM sees only sanitized, delimited text | Spec privacy rule; masks phone/UPI so those identifiers are extracted by regex, LLM cross-checks only semantic fields (agency, officer, badge, case, deadline). |
| 11 | Risk score is monotonic per conversation; payment demand under coercion floors at critical (85) | Spec: critical before/at first payment demand. Bank-ish authority scores lower (0.55) so genuine EMI calls stay low. |
| 12 | Memory acts as a risk prior: recognised script => floor `high` (seen before) or `caution+15` (seed only) | Makes "second exposure flagged earlier" a real behaviour change, not just a banner. |
| 13 | Prefix length for recognition: 3 tactics (new script), 2 once seen twice | Avoids seed patterns matching a 2-tactic legit police call. |
| 14 | Identity = random client ID header (no accounts) | Hackathon scope; documented gap in SECURITY.md. |
| 15 | Fictional identifiers use `90000 00xxx` phones, `...@examplebank` UPI, `EXMP0SIM00n` IFSC | Must be extractable by the same regexes as real ones but obviously fake. |
| 16 | App is a factory (`uvicorn app.main:create_app --factory`) | No import-time side effects (DB, key file); clean tests. |
| 17 | Replays are recorded offline-scripted runs (labelled `offline-scripted`); `make_replays.py --live` re-records with Nemotron | No key available; labelling is explicit in the UI and event stream. |
| 18 | Voice: browser Web Speech by default; NVIDIA ASR/TTS adapters env-gated and UNVERIFIED | Spec 6.8; honest about which path the demo uses (fallback unless endpoints are configured). |
| 19 | Frontend on Next 16 / React 19 (spec said Next 14) | Next 14.x has unfixed advisories incl. one critical; security over spec version. |
| 20 | `react-hooks/set-state-in-effect` lint rule disabled | Intentional post-mount reads of browser-only state to avoid hydration mismatches. |
| 21 | Held-out eval set + disclosed post-hoc awareness fix | Tuned-set metrics are optimistic; report says so. |
| 22 | Deep tier runs once per incident for final analysis + first-person complaint narrative, on sanitized, delimited text, with a deterministic fallback | Spec 2/5: strongest model for final analysis/complaint. It was missing until the handover audit. |
| 23 | `STRUCTURED_MODE=tools` reserved, not implemented | JSON-prompt + repair is the only implemented path; tool calling needs a live model to validate (backlog P1-01). |
| 24 | Report assistant never submits to cybercrime.gov.in | Portal needs the complainant's login, OTP and captcha; automating them would bypass safeguards and could file false complaints. |
| 25 | Light theme is the default; Auto/Dark available | Friendlier for elders and first impressions; HIG says support both. |

