# Deploying SCAM-KHEL

Two pieces: the **API** (FastAPI + SQLite on a persistent disk) and the **web app** (Next.js).
Nothing here needs a secret in the repo; every key is entered in the host's dashboard.

## 0. Before you start
- Rotate any key that was ever committed (see `SECURITY.md`) and generate a fresh `FERNET_KEY`:
  `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- Pick the model endpoint. Nebius Token Factory is the intended one
  (`NEBIUS_BASE_URL=https://api.tokenfactory.us-central1.nebius.com/v1/`). A key from
  build.nvidia.com only works against `https://integrate.api.nvidia.com/v1/`.
  Run `python backend/scripts/check_models.py` locally first and copy the model IDs it prints.

## 1. API on Render (about 5 minutes)
1. Render dashboard, **New, Blueprint**, pick this repo. It reads `render.yaml`.
2. Fill the prompted secrets: `NEBIUS_API_KEY`, `NEBIUS_BASE_URL`, `MODEL_FAST/MID/DEEP`,
   `FERNET_KEY`, `TAVILY_API_KEY`, `TELEGRAM_BOT_TOKEN`, and `FRONTEND_ORIGIN` (set after step 2).
3. Deploy. Check `https://<service>.onrender.com/healthz` returns ok.
   The container runs `alembic upgrade head` on start, then uvicorn on port 8000.
4. The starter plan is required for the persistent disk. On a free plan the database resets on
   every deploy, which is acceptable for a demo only.

## 2. Web app on Vercel
1. Vercel, **Add New Project**, import this repo, set **Root Directory** to `frontend`.
2. Environment variable: `NEXT_PUBLIC_API_URL=https://<service>.onrender.com`
   (build-time; redeploy after changing it).
3. Deploy, then put the resulting Vercel URL into `FRONTEND_ORIGIN` on Render and redeploy the API
   so CORS and the WebSocket origin check accept it.

## 3. After deploy
- Telegram: `python backend/scripts/set_telegram_webhook.py` with the public API URL.
- Daily cleanup: add a Render cron job running `python scripts/purge.py`.
- Keep `DEMO_MODE=true` for the public demo: it enforces the daily token budget and falls back to
  labelled offline replays when the budget is spent.
- Budget and rate limits live in memory/SQLite; with more than one instance, move them to shared storage.

## Known gaps
- The Docker images have not been built in CI. Build locally first: `docker compose build`.
- Re-check `TRUSTED_PROXIES` for your host; the value in `render.yaml` covers Render's private range.
