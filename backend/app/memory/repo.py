"""Data access: encrypted utterances, retention purge, delete-everything."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.crypto import Cipher
from app.memory.models import (
    AlertLog,
    ConsentRecord,
    EvidenceItem,
    FamilyMember,
    Incident,
    Report,
    Session,
    User,
    Utterance,
)

NOTICE_VERSION = "2026-10-v1"
CONSENT_PURPOSES = ["scam_detection", "family_alerts", "complaint_drafting"]


async def get_or_create_user(db: AsyncSession, user_id: int | None = None) -> User:
    user = await db.get(User, user_id) if user_id else None
    if user is None:
        user = User()
        db.add(user)
        await db.flush()
    return user


async def record_consent(db: AsyncSession, user_id: int) -> ConsentRecord:
    rec = ConsentRecord(user_id=user_id, notice_version=NOTICE_VERSION, purposes=CONSENT_PURPOSES)
    db.add(rec)
    await db.commit()
    return rec


async def has_consent(db: AsyncSession, user_id: int) -> bool:
    row = await db.scalar(
        select(ConsentRecord.id)
        .where(ConsentRecord.user_id == user_id, ConsentRecord.revoked_at.is_(None))
        .limit(1)
    )
    return row is not None


async def add_utterance(
    db: AsyncSession,
    cipher: Cipher,
    *,
    session_id: str,
    turn: int,
    speaker: str,
    text_plain: str,
    tactics: list[dict[str, Any]] | None = None,
    risk_after: int = 0,
) -> Utterance:
    u = Utterance(
        session_id=session_id,
        turn=turn,
        speaker=speaker,
        text_enc=cipher.encrypt(text_plain),
        tactics_json=tactics or [],
        risk_after=risk_after,
    )
    db.add(u)
    await db.flush()
    return u


async def get_utterances(
    db: AsyncSession, cipher: Cipher, session_id: str
) -> list[tuple[Utterance, str]]:
    rows = (
        await db.scalars(
            select(Utterance).where(Utterance.session_id == session_id).order_by(Utterance.turn)
        )
    ).all()
    return [(u, cipher.decrypt(u.text_enc)) for u in rows]


async def purge_older_than(db: AsyncSession, days: int) -> int:
    """Retention job: delete sessions (and their dependants) older than `days`. Returns count."""
    cutoff = datetime.now(UTC) - timedelta(days=days)
    ids = list((await db.scalars(select(Session.id).where(Session.started_at < cutoff))).all())
    await _delete_sessions(db, ids)
    await db.commit()
    return len(ids)


async def _delete_sessions(db: AsyncSession, ids: list[str]) -> None:
    if not ids:
        return
    inc_ids = select(Incident.id).where(Incident.session_id.in_(ids))
    await db.execute(delete(Report).where(Report.incident_id.in_(inc_ids)))
    await db.execute(delete(Incident).where(Incident.session_id.in_(ids)))
    await db.execute(delete(EvidenceItem).where(EvidenceItem.session_id.in_(ids)))
    await db.execute(delete(Utterance).where(Utterance.session_id.in_(ids)))
    await db.execute(delete(Session).where(Session.id.in_(ids)))


async def delete_user_data(db: AsyncSession, user_id: int) -> None:
    """'Delete everything' for a user. Learned seed/library scripts hold no personal data
    (only normalised tactic sequences/phrases), but user-derived learned scripts are removed
    too if they were learned solely from this user's incidents."""
    ids = list((await db.scalars(select(Session.id).where(Session.user_id == user_id))).all())
    inc_ids = list(
        (await db.scalars(select(Incident.id).where(Incident.session_id.in_(ids)))).all()
    )
    await _delete_sessions(db, ids)
    await db.execute(delete(AlertLog).where(AlertLog.user_id == user_id))
    await db.execute(delete(FamilyMember).where(FamilyMember.user_id == user_id))
    await db.execute(delete(ConsentRecord).where(ConsentRecord.user_id == user_id))
    await db.execute(delete(User).where(User.id == user_id))
    if inc_ids:  # drop learned (non-seed) scripts whose only source was a deleted incident
        from app.memory.models import ScamScript

        orphan = (
            await db.scalars(
                select(ScamScript).where(
                    ScamScript.is_seed.is_(False), ScamScript.first_incident_id.in_(inc_ids)
                )
            )
        ).all()
        for s in orphan:
            still_used = await db.scalar(
                select(Incident.id).where(Incident.recognised_script_id == s.id).limit(1)
            )
            if still_used:  # another user's incident relies on it; it holds no personal data
                continue
            await db.execute(text("DELETE FROM script_fts WHERE script_id = :i"), {"i": s.id})
            await db.delete(s)
    await db.commit()
