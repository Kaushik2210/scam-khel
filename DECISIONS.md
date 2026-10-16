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
