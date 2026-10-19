from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select

from app.actions.report_fields import build_report_fields
from app.api.helpers import complaint_from_db, incident_for_user
from app.api.schemas import FeedbackIn
from app.api.state import AppState, current_user
from app.memory import repo
from app.memory.models import (
    EvidenceItem,
    Incident,
    IncidentFeedback,
    ScamScript,
    Session,
    User,
)

router = APIRouter()
UserDep = tuple[AppState, User]


@router.get("/api/memory/scripts")
async def scripts(ctx: UserDep = Depends(current_user)) -> list[dict[str, Any]]:
    st, _ = ctx
    async with st.sm() as db:
        rows = (await db.scalars(select(ScamScript).order_by(ScamScript.seen_count.desc()))).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "tactic_sequence": s.tactic_sequence,
            "phrases": s.phrases[:6],
            "seen_count": s.seen_count,
            "seed": s.is_seed,
            "first_seen": s.first_seen.isoformat(),
            "last_seen": s.last_seen.isoformat(),
        }
        for s in rows
    ]


@router.get("/api/incidents")
async def incidents(ctx: UserDep = Depends(current_user)) -> list[dict[str, Any]]:
    st, user = ctx
    async with st.sm() as db:
        rows = (
            await db.execute(
                select(Incident, Session)
                .join(Session, Session.id == Incident.session_id)
                .where(Session.user_id == user.id)
                .order_by(Incident.id.desc())
                .limit(100)
            )
        ).all()
    return [
        {
            "id": i.id,
            "session_id": i.session_id,
            "summary": i.summary,
            "created": i.created_at.isoformat(),
            "risk_peak": s.risk_peak,
            "mode": s.mode,
            "scenario": (i.data or {}).get("scenario"),
            "detect_turn": i.detect_turn,
            "memory_hit_turn": i.memory_hit_turn,
            "recognised_script_id": i.recognised_script_id,
            "feedback_verdict": i.feedback_verdict,
        }
        for i, s in rows
    ]


@router.get("/api/incidents/{incident_id}")
async def incident(incident_id: int, ctx: UserDep = Depends(current_user)) -> dict[str, Any]:
    st, user = ctx
    async with st.sm() as db:
        found = await incident_for_user(db, user.id, incident_id=incident_id)
        if not found:
            raise HTTPException(404, "not found")
        inc, sess = found
        utts = await repo.get_utterances(db, st.cipher, sess.id)
        ev = (
            await db.scalars(select(EvidenceItem).where(EvidenceItem.session_id == sess.id))
        ).all()
        script = (
            await db.get(ScamScript, inc.recognised_script_id) if inc.recognised_script_id else None
        )
    d = inc.data or {}
    return {
        "id": inc.id,
        "session_id": sess.id,
        "summary": inc.summary,
        "risk_peak": sess.risk_peak,
        "time_wasted_s": sess.time_wasted_s,
        "detect_turn": inc.detect_turn,
        "memory_hit_turn": inc.memory_hit_turn,
        "script": script.name if script else None,
        "feedback_verdict": inc.feedback_verdict,
        "simulation": d.get("simulation", True),
        "scenario": d.get("scenario"),
        "timeline": d.get("timeline", []),
        "verifications": d.get("verifications", []),
        "final_analysis": d.get("final_analysis"),
        "transcript": [{"turn": u.turn, "speaker": u.speaker, "text": t} for u, t in utts],
        "evidence": [
            {"type": e.type, "value": e.value, "confidence": round(e.confidence, 2)} for e in ev
        ],
    }


@router.post("/api/incidents/{incident_id}/feedback")
async def incident_feedback(
    incident_id: int, body: FeedbackIn, ctx: UserDep = Depends(current_user)
) -> dict[str, Any]:
    """Store user feedback: 'scam' or 'not_scam' (false positive) to calibrate detection."""
    st, user = ctx
    async with st.sm() as db:
        found = await incident_for_user(db, user.id, incident_id=incident_id)
        if not found:
            raise HTTPException(404, "not found")
        inc, _ = found
        inc.feedback_verdict = body.verdict
        fb = IncidentFeedback(
            incident_id=inc.id,
            verdict=body.verdict,
            notes=body.notes,
        )
        db.add(fb)
        await db.commit()
    return {"id": incident_id, "verdict": body.verdict, "saved": True}


@router.get("/api/memory/feedback-stats")
async def feedback_stats(ctx: UserDep = Depends(current_user)) -> dict[str, Any]:
    """Return user feedback calibration counts (confirmed scams vs false alarms)."""
    st, user = ctx
    async with st.sm() as db:
        total_scam = (
            await db.scalar(
                select(func.count(IncidentFeedback.id))
                .join(Incident, Incident.id == IncidentFeedback.incident_id)
                .join(Session, Session.id == Incident.session_id)
                .where(Session.user_id == user.id, IncidentFeedback.verdict == "scam")
            )
            or 0
        )
        total_not_scam = (
            await db.scalar(
                select(func.count(IncidentFeedback.id))
                .join(Incident, Incident.id == IncidentFeedback.incident_id)
                .join(Session, Session.id == Incident.session_id)
                .where(Session.user_id == user.id, IncidentFeedback.verdict == "not_scam")
            )
            or 0
        )
    return {
        "confirmed_scams": int(total_scam),
        "false_alarms": int(total_not_scam),
        "total_feedback": int(total_scam + total_not_scam),
    }


@router.delete("/api/me/data")
async def delete_me(ctx: UserDep = Depends(current_user)) -> dict[str, bool]:
    st, user = ctx
    async with st.sm() as db:
        await repo.delete_user_data(db, user.id)
    for k in [k for k, v in st.live.items() if v.user_id == user.id]:
        st.live[k].stop.set()
        del st.live[k]
    return {"deleted": True}


@router.get("/api/incidents/{incident_id}/report-fields")
async def report_fields(
    incident_id: int, redact: bool = True, ctx: UserDep = Depends(current_user)
) -> dict[str, Any]:
    """Structured, copy-ready fields for cybercrime.gov.in (the app never submits anything)."""
    st, user = ctx
    async with st.sm() as db:
        found = await incident_for_user(db, user.id, incident_id=incident_id)
        if not found:
            raise HTTPException(404, "not found")
        data = await complaint_from_db(db, st, *found)
    return build_report_fields(data, redact)
