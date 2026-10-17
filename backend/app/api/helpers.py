from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.actions.alerts import AlertService
from app.actions.complaint import ComplaintData
from app.api.state import AppState
from app.memory import repo
from app.memory.models import EvidenceItem, Incident, Session, UsageLog
from app.orchestrator import AlertHook, Emit


def make_alert_hook(st: AppState, user_id: int, emit: Emit, simulation: bool) -> AlertHook:
    async def hook(level: str, payload: dict[str, Any]) -> None:
        async with st.sm() as db:
            svc = AlertService(db, st.telegram, st.settings.frontend_origin)
            res = await svc.send_family_alert(
                user_id=user_id,
                session_id=payload.get("session_id"),
                level=level,
                tactics=payload.get("tactics", []),
                summary=(
                    f"A call is showing scam tactics (risk {payload.get('score')}/100)."
                    if not simulation
                    else f"Simulation: risk reached {payload.get('score')}/100."
                ),
                simulation=simulation,
            )
        await emit(
            "alert_sent",
            {"level": level, "sent": res.sent, "skipped": res.skipped, "errors": res.errors},
        )

    return hook


async def flush_usage(st: AppState) -> None:
    recs = st.tracker.records[st.usage_flushed :]
    if not recs:
        return
    async with st.sm() as db:
        for r in recs:
            db.add(
                UsageLog(
                    model_tier=r.tier,
                    model=r.model,
                    prompt_tokens=r.prompt_tokens,
                    completion_tokens=r.completion_tokens,
                    latency_ms=r.latency_ms,
                )
            )
        await db.commit()
    st.usage_flushed += len(recs)


async def incident_for_user(
    db: AsyncSession, user_id: int, *, incident_id: int | None = None, session_id: str | None = None
) -> tuple[Incident, Session] | None:
    q = select(Incident, Session).join(Session, Session.id == Incident.session_id)
    q = q.where(Session.user_id == user_id)
    q = (
        q.where(Incident.id == incident_id)
        if incident_id
        else q.where(Incident.session_id == session_id)
    )
    row = (await db.execute(q)).first()
    return (row[0], row[1]) if row else None


async def complaint_from_db(
    db: AsyncSession, st: AppState, inc: Incident, sess: Session
) -> ComplaintData:
    utts = await repo.get_utterances(db, st.cipher, sess.id)
    ev = (await db.scalars(select(EvidenceItem).where(EvidenceItem.session_id == sess.id))).all()
    data = inc.data or {}
    return ComplaintData(
        incident_id=inc.id,
        scenario=data.get("scenario", sess.scenario or "unknown"),
        simulation=bool(data.get("simulation", True)),
        risk_peak=sess.risk_peak,
        summary=inc.summary,
        timeline=data.get("timeline", []),
        evidence=[
            {"type": e.type, "value": e.value, "confidence": round(e.confidence, 2), "mentions": 1}
            for e in ev
        ],
        transcript=[{"turn": u.turn, "speaker": u.speaker, "text": t} for u, t in utts],
        verifications=data.get("verifications", []),
    )
