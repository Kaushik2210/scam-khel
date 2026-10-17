from __future__ import annotations

import secrets
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.actions.alerts import AlertService
from app.actions.telegram import handle_update
from app.api.schemas import FamilyIn
from app.api.state import AppState, current_user, get_state
from app.memory import repo
from app.memory.models import User

router = APIRouter()
UserDep = tuple[AppState, User]


@router.get("/api/family")
async def family(ctx: UserDep = Depends(current_user)) -> dict[str, Any]:
    st, user = ctx
    async with st.sm() as db:
        members = await repo.list_family(db, user.id)
    return {
        "telegram_configured": st.telegram.configured,
        "members": [
            {
                "id": m.id,
                "label": m.label,
                "role": m.role,
                "join_code": m.join_code,
                "linked": m.telegram_chat_id is not None,
            }
            for m in members
        ],
        "join_help": "Ask each family member to message the bot: /start <their code>",
    }


@router.post("/api/family")
async def add_family(body: FamilyIn, ctx: UserDep = Depends(current_user)) -> dict[str, Any]:
    st, user = ctx
    async with st.sm() as db:
        if len(await repo.list_family(db, user.id)) >= 10:
            raise HTTPException(400, "Family circle is limited to 10 members.")
        m = await repo.add_family_member(db, user.id, body.label, body.role)
    return {"id": m.id, "label": m.label, "join_code": m.join_code}


@router.post("/api/family/test-alert")
async def test_alert(ctx: UserDep = Depends(current_user)) -> dict[str, Any]:
    st, user = ctx
    if not st.telegram.configured:
        raise HTTPException(503, "Telegram is not configured (TELEGRAM_BOT_TOKEN).")
    async with st.sm() as db:
        res = await AlertService(db, st.telegram, st.settings.frontend_origin).send_family_alert(
            user.id,
            f"test-{secrets.token_hex(4)}",
            "high",
            ["fear_arrest_threat"],
            "This is a TEST alert from SCAM-KHEL. No action needed.",
            simulation=True,
            force=True,
        )
    return {"sent": res.sent, "skipped": res.skipped, "errors": res.errors}


@router.post("/api/telegram/webhook")
async def webhook(
    request: Request, x_telegram_bot_api_secret_token: str = Header(default="")
) -> dict[str, bool]:
    st = get_state(request)
    secret = st.settings.admin_token
    if not secret or not secrets.compare_digest(x_telegram_bot_api_secret_token, secret):
        raise HTTPException(403, "forbidden")
    update = await request.json()
    async with st.sm() as db:
        await handle_update(update, db, st.telegram)
    return {"ok": True}
