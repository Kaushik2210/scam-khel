"""Family alerts: deduped, rate-limited, escalate critical once, every attempt logged."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.actions.telegram import TelegramClient, TelegramError
from app.detect.taxonomy import TACTICS
from app.logging import get_logger
from app.memory.models import AlertLog, FamilyMember

log = get_logger("alerts")
MAX_ALERTS_PER_HOUR = 5

LEVEL_TEXT = {"high": "HIGH RISK", "critical": "CRITICAL", "money_sent": "MONEY ALREADY SENT"}


@dataclass
class AlertResult:
    sent: int
    skipped: str | None = None  # duplicate | rate_limited | no_recipients | not_configured
    errors: int = 0


def format_alert(
    level: str, tactics: list[str], summary: str, link: str, simulation: bool = False
) -> str:
    names = ", ".join(TACTICS[t].description.rstrip(".") for t in tactics[:4] if t in TACTICS)
    head = f"{'[SIMULATION] ' if simulation else ''}SCAM-KHEL alert: {LEVEL_TEXT.get(level, level)}"
    lines = [head, "", summary]
    if names:
        lines += ["", f"What we noticed: {names}."]
    lines += [
        "",
        "Call your parent now. Tell them to hang up: police, CBI, ED and courts do not arrest "
        "anyone over a video call. If money was sent, call 1930 immediately.",
        f"Details: {link}",
    ]
    return "\n".join(lines)


class AlertService:
    def __init__(self, db: AsyncSession, telegram: TelegramClient, frontend_url: str) -> None:
        self.db, self.tg, self.frontend_url = db, telegram, frontend_url.rstrip("/")

    async def _recipients(self, user_id: int) -> list[FamilyMember]:
        rows = await self.db.scalars(
            select(FamilyMember).where(
                FamilyMember.user_id == user_id, FamilyMember.telegram_chat_id.is_not(None)
            )
        )
        return list(rows.all())

    async def send_family_alert(
        self,
        user_id: int,
        session_id: str | None,
        level: str,
        tactics: list[str],
        summary: str,
        incident_id: int | None = None,
        simulation: bool = False,
        force: bool = False,
    ) -> AlertResult:
        if not self.tg.configured:
            return AlertResult(0, "not_configured")
        key = f"{session_id or 'none'}:{level}"
        if not force:
            dup = await self.db.scalar(
                select(AlertLog.id).where(
                    AlertLog.user_id == user_id, AlertLog.dedupe_key == key, AlertLog.ok.is_(True)
                )
            )
            if dup:
                return AlertResult(0, "duplicate")
            since = datetime.now(UTC) - timedelta(hours=1)
            recent = await self.db.scalar(
                select(func.count(AlertLog.id)).where(
                    AlertLog.user_id == user_id, AlertLog.ok.is_(True), AlertLog.sent_at > since
                )
            )
            if (recent or 0) >= MAX_ALERTS_PER_HOUR:
                return AlertResult(0, "rate_limited")
        members = await self._recipients(user_id)
        if not members:
            return AlertResult(0, "no_recipients")
        link = f"{self.frontend_url}/incidents/{incident_id}" if incident_id else self.frontend_url
        text = format_alert(level, tactics, summary, link, simulation)
        sent = errors = 0
        for m in members:
            ok = False
            try:
                await self.tg.send_message(str(m.telegram_chat_id), text)
                ok = True
                sent += 1
            except TelegramError as e:
                errors += 1
                log.warning("alert_send_failed", error=str(e)[:160])
            self.db.add(
                AlertLog(
                    user_id=user_id,
                    session_id=session_id,
                    level=level,
                    channel="telegram",
                    dedupe_key=key,
                    ok=ok,
                )
            )
        await self.db.commit()
        return AlertResult(sent, None, errors)
