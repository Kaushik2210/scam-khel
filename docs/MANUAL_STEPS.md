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

## Added during the build
- [ ] After keys are set: `make check-models` -> commit the real `docs/model_report.md`; set `STRUCTURED_MODE` as it recommends.
- [ ] `make eval-live` -> commit `backend/evals/report.md` (fills the token/latency table); `python backend/scripts/make_replays.py --live` to re-record replays with real Nemotron output.
- [ ] Telegram: create the bot, set `TELEGRAM_BOT_TOKEN`, set the webhook to `https://<api>/api/telegram/webhook` with secret token = `ADMIN_TOKEN` (Telegram `setWebhook`), link your phone in `/family`, press "Send test alert".
- [ ] Deploy: Vercel (root `frontend`, env `NEXT_PUBLIC_API_URL`), backend container with volume `/data`, env `DEMO_MODE=true FRONTEND_ORIGIN=<vercel url> FERNET_KEY ADMIN_TOKEN NEBIUS_* MODEL_* TAVILY_API_KEY`; cron `python scripts/purge.py` daily.
- [ ] Confirm `docker compose up --build` works (Docker was not available on the dev machine).
- [ ] Add screenshots/GIF to `docs/screenshots/` and README; record and time the demo (<= 3:00); do one dry run with real keys.
- [ ] Install gitleaks locally and run it over history; enable branch protection.
- [ ] Verify the repo license shows as MIT on GitHub; make the repo public.
