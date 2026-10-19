from __future__ import annotations

import uuid
from datetime import date, time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.actions import blocklist
from app.actions.complaint import build_markdown
from app.actions.panic import TransactionDetails, panic_bundle
from app.actions.pdf import render_pdf
from app.api.helpers import complaint_from_db, flush_usage, incident_for_user, make_alert_hook
from app.api.schemas import AnalyzeIn, PanicIn, SessionIn
from app.api.state import AppState, LiveSession, client_ip, current_user
from app.memory import repo
from app.memory.models import User
from app.shield import ShieldAnalyzer
from app.simulator.scenario import list_scenarios, load_scenario

router = APIRouter()
UserDep = tuple[AppState, User]


def _limit(st: AppState, request: Request, bucket: str, limit: int, window: float) -> None:
    ip = client_ip(request)
    if not st.limiter.allow(f"{bucket}:{ip}", limit, window):
        raise HTTPException(
            429,
            "Too many requests",
            headers={"Retry-After": str(st.limiter.retry_after(f"{bucket}:{ip}", window))},
        )


@router.get("/api/scenarios")
async def scenarios() -> list[dict[str, Any]]:
    return [
        {"id": s.id, "title": s.title, "language": s.language, "agency": s.agency}
        for s in list_scenarios()
    ]


@router.post("/api/sessions")
async def create_session(
    body: SessionIn, request: Request, ctx: UserDep = Depends(current_user)
) -> dict[str, Any]:
    st, user = ctx
    if not body.consent:
        raise HTTPException(400, "Consent is required before any analysis or recording.")
    s = st.settings
    _limit(st, request, "sessions", s.per_ip_sessions_per_hour, 3600)
    if body.mode != "shield":
        try:
            load_scenario(body.scenario)
        except KeyError:
            raise HTTPException(404, "unknown scenario") from None
    st.gc_live()
    if len(st.live) >= 50:
        raise HTTPException(503, "Server is busy, try again shortly.")
    async with st.sm() as db:
        if not await repo.has_consent(db, user.id):
            await repo.record_consent(db, user.id)
    sid = str(uuid.uuid4())
    live = LiveSession(sid, user.id, body.mode, body.scenario, body.language)
    st.live[sid] = live
    exhausted = st.budget.exhausted
    return {
        "id": sid,
        "ws": f"/ws/sessions/{sid}",
        "ws_ticket": live.ticket,
        "mode": body.mode,
        "simulation": body.mode != "shield",
        "replay": exhausted,
        "max_turns": s.max_turns_per_session if s.demo_mode else 30,
        "llm_mode": st.llm_mode,
        "notice": "Budget exhausted: showing a recorded replay." if exhausted else None,
    }


@router.post("/api/sessions/{sid}/end")
async def end_session(sid: str, ctx: UserDep = Depends(current_user)) -> dict[str, Any]:
    st, user = ctx
    live = st.live.get(sid)
    if live is None or live.user_id != user.id:
        raise HTTPException(404, "unknown session")
    live.stop.set()
    await live.inbox.put(None)
    return {"ended": True, "summary": live.summary}


async def _complaint(sid: str, ctx: UserDep, redact: bool):  # type: ignore[no-untyped-def]
    st, user = ctx
    async with st.sm() as db:
        found = await incident_for_user(db, user.id, session_id=sid)
        if not found:
            raise HTTPException(404, "No incident for this session yet (end the session first).")
        return await complaint_from_db(db, st, *found)


@router.get("/api/sessions/{sid}/complaint.md")
async def complaint_md(
    sid: str, redact: bool = True, ctx: UserDep = Depends(current_user)
) -> Response:
    data = await _complaint(sid, ctx, redact)
    return Response(
        build_markdown(data, redact),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="complaint-draft.md"'},
    )


@router.get("/api/sessions/{sid}/complaint.pdf")
async def complaint_pdf(
    sid: str, redact: bool = True, ctx: UserDep = Depends(current_user)
) -> Response:
    data = await _complaint(sid, ctx, redact)
    return Response(
        render_pdf(data, redact),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="complaint-draft.pdf"'},
    )


@router.post("/api/analyze")
async def analyze(
    body: AnalyzeIn, request: Request, ctx: UserDep = Depends(current_user)
) -> dict[str, Any]:
    """One-shot Shield analysis of pasted text or a list of turns."""
    st, user = ctx
    if not body.consent:
        raise HTTPException(400, "Consent is required before any analysis.")
    _limit(st, request, "analyze", 30, 60)
    if st.budget.exhausted:
        # rules-only analysis costs no tokens, so Shield stays fully available
        llm = None
    else:
        llm = st.llm
    turns: list[tuple[str, str]] = [(t.s, t.t) for t in body.turns] if body.turns else []
    if not turns:
        if not body.text or not body.text.strip():
            raise HTTPException(422, "Provide `text` or `turns`.")
        turns = [("caller", chunk.strip()) for chunk in body.text.split("\n") if chunk.strip()][:60]
    sid = str(uuid.uuid4())
    async with st.sm() as db:
        if not await repo.has_consent(db, user.id):
            await repo.record_consent(db, user.id)
        sh = ShieldAnalyzer(
            llm, session_id=sid, db=db, cipher=st.cipher, user_id=user.id, language=body.language
        )
        for who, text in turns:
            await sh.feed(text, who)
        res = await sh.finish()
    await flush_usage(st)
    return {
        "session_id": sid,
        "incident_id": res.incident_id,
        "score": res.score,
        "level": res.level,
        "stage": res.stage,
        "tactics": res.tactics,
        "explanation": res.explanation,
        "evidence": res.evidence,
        "detect_turn": res.detect_turn,
        "memory_hit": res.memory_hit,
        "timeline": res.timeline,
        "llm_mode": "nemotron-token-factory" if llm else "rules-only",
    }


@router.post("/api/panic")
async def panic(
    body: PanicIn, request: Request, ctx: UserDep = Depends(current_user)
) -> dict[str, Any]:
    st, user = ctx
    _limit(st, request, "panic", 20, 60)
    try:
        tx = TransactionDetails(
            amount_inr=body.amount_inr,
            txn_date=date.fromisoformat(body.txn_date) if body.txn_date else None,
            txn_time=time.fromisoformat(body.txn_time) if body.txn_time else None,
            mode=body.mode,
            beneficiary_name=body.beneficiary_name,
            beneficiary_account_or_upi=body.beneficiary_account_or_upi,
            bank_name=body.bank_name,
            txn_reference=body.txn_reference,
            caller_phone=body.caller_phone,
        )
    except ValueError as e:
        raise HTTPException(422, f"invalid transaction details: {e}") from None
    incident = None
    if body.session_id:
        async with st.sm() as db:
            found = await incident_for_user(db, user.id, session_id=body.session_id)
            if found:
                incident = await complaint_from_db(db, st, *found)
    bundle = panic_bundle(tx, body.language, incident)

    async def _noop(_t: str, _p: dict[str, Any]) -> None:
        return None

    hook = make_alert_hook(st, user.id, _noop, simulation=False)
    await hook(
        "money_sent",
        {
            "session_id": body.session_id or f"panic-{uuid.uuid4()}",
            "score": 100,
            "tactics": ["safe_account_transfer"],
        },
    )
    return bundle


@router.get("/api/blocklist.csv")
async def blocklist_csv(ctx: UserDep = Depends(current_user)) -> Response:
    ev = await _all_evidence(ctx)
    return Response(
        blocklist.to_csv(ev),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="blocklist.csv"'},
    )


@router.get("/api/blocklist.json")
async def blocklist_json(ctx: UserDep = Depends(current_user)) -> Response:
    ev = await _all_evidence(ctx)
    return Response(blocklist.to_json(ev), media_type="application/json")


async def _all_evidence(ctx: UserDep) -> list[dict[str, Any]]:
    from sqlalchemy import select

    from app.memory.models import EvidenceItem, Session

    st, user = ctx
    async with st.sm() as db:
        rows = (
            await db.scalars(
                select(EvidenceItem)
                .join(Session, Session.id == EvidenceItem.session_id)
                .where(Session.user_id == user.id)
            )
        ).all()
    return [
        {"type": r.type, "value": r.value, "confidence": r.confidence, "mentions": 1} for r in rows
    ]
