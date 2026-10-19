"""Configure the Telegram bot webhook for incoming family join (/start <code>) updates.

Usage:
    python backend/scripts/set_telegram_webhook.py --url https://<your-host>/api/telegram/webhook
    python backend/scripts/set_telegram_webhook.py --delete
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.actions.telegram import TelegramClient, TelegramError
from app.config import get_settings


async def main() -> None:
    parser = argparse.ArgumentParser(description="Configure Telegram Bot webhook.")
    parser.add_argument("--url", help="Public HTTPS URL for webhook (e.g. https://api.example.com/api/telegram/webhook)")
    parser.add_argument("--secret", help="Secret token for Telegram webhook validation (defaults to ADMIN_TOKEN in env)")
    parser.add_argument("--token", help="Telegram bot token (defaults to TELEGRAM_BOT_TOKEN in env)")
    parser.add_argument("--delete", action="store_true", help="Remove existing webhook")
    args = parser.parse_args()

    settings = get_settings()
    token = args.token or settings.telegram_bot_token
    secret = args.secret or settings.admin_token

    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN is not set in .env or passed via --token.", file=sys.stderr)
        print("Create a bot via @BotFather and set TELEGRAM_BOT_TOKEN. See docs/MANUAL_STEPS.md.", file=sys.stderr)
        sys.exit(1)

    client = TelegramClient(token)

    if args.delete:
        print("Deleting Telegram webhook...")
        try:
            res = await client._call("deleteWebhook", {"drop_pending_updates": False})
            print("Webhook deleted successfully:", res.get("description", "OK"))
        except TelegramError as e:
            print(f"Failed to delete webhook: {e}", file=sys.stderr)
            sys.exit(1)
        return

    url = args.url
    if not url:
        print("ERROR: --url is required unless --delete is specified.", file=sys.stderr)
        print("Example: python scripts/set_telegram_webhook.py --url https://my-app.onrender.com/api/telegram/webhook", file=sys.stderr)
        sys.exit(1)

    if not url.startswith("https://"):
        print("WARNING: Telegram requires an HTTPS webhook URL in production.", file=sys.stderr)

    print(f"Setting webhook to: {url}")
    try:
        await client.set_webhook(url=url, secret=secret)
        print("Telegram webhook configured successfully!")
        info = await client._call("getWebhookInfo", {})
        result = info.get("result", {})
        print(f"Current webhook status: URL={result.get('url')} (pending updates: {result.get('pending_update_count', 0)})")
    except TelegramError as e:
        print(f"Failed to set webhook: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
