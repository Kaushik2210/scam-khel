"""Telegram Bot API client (plain httpx) + /start <code> family-join handling."""

from __future__ import annotations

from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging import get_logger
from app.memory.models import FamilyMember

log = get_logger("telegram")
API = "https://api.telegram.org"


class TelegramError(RuntimeError):
    pass


class TelegramClient:
    def __init__(self, token: str, http: httpx.AsyncClient | None = None) -> None:
        self.token = token
        self._http = http

    @property
    def configured(self) -> bool:
        return bool(self.token)

    async def _call(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.token:
            raise TelegramError("TELEGRAM_BOT_TOKEN is not set (see docs/MANUAL_STEPS.md)")
        http = self._http or httpx.AsyncClient(timeout=10)
        try:
            r = await http.post(f"{API}/bot{self.token}/{method}", json=payload)
        except httpx.HTTPError as e:
            raise TelegramError(f"network error: {type(e).__name__}") from e
        finally:
            if self._http is None:
                await http.aclose()
        data: dict[str, Any] = r.json() if r.content else {}
        if r.status_code != 200 or not data.get("ok"):
            # never log the token: only status and Telegram's description
            raise TelegramError(f"{method} failed: {r.status_code} {data.get('description', '')}")
        return data

    async def send_message(self, chat_id: str, text: str) -> None:
        await self._call(
            "sendMessage",
            {"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
        )

    async def set_webhook(self, url: str, secret: str) -> None:
        await self._call("setWebhook", {"url": url, "secret_token": secret})


async def handle_update(
    update: dict[str, Any], db: AsyncSession, client: TelegramClient
) -> str | None:
    """Process one Telegram update. '/start <code>' links the chat to a family member."""
    msg = update.get("message") or {}
    text = (msg.get("text") or "").strip()
    chat_id = str((msg.get("chat") or {}).get("id", ""))
    if not chat_id or not text.startswith("/start"):
        return None
    parts = text.split()
    if len(parts) < 2:
        await client.send_message(
            chat_id, "Send /start <code> using the code from the SCAM-KHEL app."
        )
        return "missing_code"
    member = await db.scalar(select(FamilyMember).where(FamilyMember.join_code == parts[1][:16]))
    if member is None:
        await client.send_message(chat_id, "That code was not recognised. Check it in the app.")
        return "unknown_code"
    member.telegram_chat_id = chat_id
    await db.commit()
    await client.send_message(
        chat_id,
        "You are now linked to the family safety circle. You will get an alert here if a "
        "suspicious call is detected. (SCAM-KHEL)",
    )
    return "linked"
