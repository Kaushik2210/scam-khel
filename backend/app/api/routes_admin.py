from __future__ import annotations

import secrets
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request

from app.api.state import get_state
from app.guards.demo_mode import list_replays

router = APIRouter()


@router.get("/healthz")
async def healthz(request: Request) -> dict[str, Any]:
    st = get_state(request)
    return {
        "ok": True,
        "demo_mode": st.settings.demo_mode,
        "llm_mode": st.llm_mode,
        "budget": st.budget.status() if st.settings.demo_mode else None,
        "telegram": st.telegram.configured,
        "tavily": st.verifier.available,
    }


@router.get("/api/models/status")
async def models_status(request: Request) -> dict[str, Any]:
    st, s = get_state(request), get_state(request).settings
    return {
        "provider": "Nebius Token Factory (OpenAI-compatible)",
        "mode": st.llm_mode,
        "structured_mode": s.structured_mode,
        "tiers": {
            "fast": {
                "model": s.model_fast or None,
                "does": "per-utterance tactic tagging, injection screening",
            },
            "mid": {
                "model": s.model_mid or None,
                "does": "honeypot persona, scammer simulator, evidence cross-check",
            },
            "deep": {
                "model": s.model_deep or None,
                "does": "final analysis and complaint narrative",
            },
        },
        "note": None if st.llm else "Offline mode: rules + scripted fallbacks only (no LLM calls).",
    }


@router.get("/api/admin/usage")
async def usage(request: Request, x_admin_token: str = Header(default="")) -> dict[str, Any]:
    st = get_state(request)
    token = st.settings.admin_token
    if not token or not secrets.compare_digest(x_admin_token, token):
        raise HTTPException(403, "forbidden")
    return {"by_tier": st.tracker.summary(), "budget": st.budget.status()}


@router.get("/api/replays")
async def replays() -> list[dict[str, Any]]:
    return list_replays()
