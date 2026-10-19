"""Telegram Bot API client (plain httpx) + /start <code> family-join handling."""

from __future__ import annotations

from typing import Any

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.guards.ratelimit import RateLimiter
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


MAX_BAD_CODES = 5  # wrong codes per chat per hour before that chat is locked out
BAD_CODE_WINDOW_S = 3600


async def handle_update(
    update: dict[str, Any],
    db: AsyncSession,
    client: TelegramClient,
    limiter: RateLimiter | None = None,
) -> str | None:
    """Process one Telegram update. '/start <code>' links the chat to a family member.

    A code links one chat. Once linked, a different chat cannot take the slot over with the
    same code, and a chat that keeps sending wrong codes is locked out for a while.
    """
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
    attempts_key = f"tg-join:{chat_id}"
    if limiter and limiter.exhausted(attempts_key, MAX_BAD_CODES, BAD_CODE_WINDOW_S):
        await client.send_message(chat_id, "Too many wrong codes. Please try again later.")
        return "rate_limited"
    code = parts[1][:16].upper()
    member = await db.scalar(select(FamilyMember).where(func.upper(FamilyMember.join_code) == code))
    if member is None:
        if limiter:
            limiter.allow(attempts_key, MAX_BAD_CODES, BAD_CODE_WINDOW_S)
        await client.send_message(chat_id, "That code was not recognised. Check it in the app.")
        return "unknown_code"
    if member.telegram_chat_id and member.telegram_chat_id != chat_id:
        await client.send_message(
            chat_id,
            "That code is already in use. Ask the person who invited you to remove the entry "
            "in the app and add you again.",
        )
        return "already_linked"
    member.telegram_chat_id = chat_id
    await db.commit()
    await client.send_message(
        chat_id,
        "You are now linked to the family safety circle. You will get an alert here if a "
        "suspicious call is detected. (SCAM-KHEL)",
    )
    return "linked"
