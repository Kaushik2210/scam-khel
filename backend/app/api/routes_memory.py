from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.actions.report_fields import build_report_fields
from app.api.helpers import complaint_from_db, incident_for_user
from app.api.state import AppState, current_user
from app.memory import repo
from app.memory.models import EvidenceItem, Incident, ScamScript, Session, User

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
        "simulation": d.get("simulation", True),
        "scenario": d.get("scenario"),
        "timeline": d.get("timeline", []),
        "verifications": d.get("verifications", []),
        "transcript": [{"turn": u.turn, "speaker": u.speaker, "text": t} for u, t in utts],
        "evidence": [
            {"type": e.type, "value": e.value, "confidence": round(e.confidence, 2)} for e in ev
        ],
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
