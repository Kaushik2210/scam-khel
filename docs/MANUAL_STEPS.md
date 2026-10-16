# Manual steps (only you can do these)

- [ ] Create a Nebius Token Factory account, API key; claim credits with code `NEBIUS-DEVPOST-GLOBAL26`; join the Nebius Builders Program.
- [ ] Put the key in `.env` (`NEBIUS_API_KEY`), confirm `NEBIUS_BASE_URL` in the dashboard.
- [ ] Run `make check-models`, pick Nemotron IDs for `MODEL_FAST/MID/DEEP`, set `STRUCTURED_MODE` as recommended in `docs/model_report.md`.
- [ ] Create a Tavily key (`TAVILY_API_KEY`).
- [ ] Create a Telegram bot via @BotFather (`TELEGRAM_BOT_TOKEN`).
- [ ] Generate `FERNET_KEY` (command in `.env.example`) and `ADMIN_TOKEN`.
- [ ] Install gitleaks locally (`pre-commit install`) and Docker (not present on the dev machine).
- [ ] Create the public GitHub repo, push, confirm MIT license shows in About.
- [ ] Deploy (Vercel + container host), record ≤3 min demo on YouTube, submit on Devpost, fill the feedback form from `FEEDBACK_DRAFT.md`.
