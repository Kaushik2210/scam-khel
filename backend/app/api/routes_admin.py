from __future__ import annotations

import secrets
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request

from app.api.state import client_ip, get_state
from app.guards.demo_mode import list_replays
from app.voice.asr import MAX_AUDIO_BYTES, AudioTooLarge, HttpTranscriptionASR, voice_status

router = APIRouter()


@router.get("/api/voice/status")
async def voice(request: Request) -> dict[str, Any]:
    s = get_state(request).settings
    return voice_status(s.asr_base_url, s.tts_base_url)


@router.post("/api/voice/transcribe")
async def transcribe_audio(
    request: Request,
    language: str = "en",
) -> dict[str, Any]:
    """Server-side speech-to-text adapter (NVIDIA Parakeet / Nemotron-speech).

    Takes audio bytes directly in the request body.
    Audio is processed in-memory and immediately discarded; it is never written to disk.
    """
    st = get_state(request)
    s = st.settings
    ip = client_ip(request)
    if not st.limiter.allow(f"asr_{ip}", limit=30, window_s=60):
        raise HTTPException(429, "Too many transcription requests. Please wait a moment.")

    audio_bytes = await request.body()
    if not audio_bytes:
        raise HTTPException(400, "Empty audio payload.")
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(
            413, f"Audio clip exceeds maximum size of {MAX_AUDIO_BYTES // (1024 * 1024)}MB."
        )

    if not s.asr_base_url:
        raise HTTPException(
            501,
            "Server-side NVIDIA ASR endpoint not configured. Set ASR_BASE_URL or use browser Web Speech fallback.",
        )

    asr = HttpTranscriptionASR(
        base_url=s.asr_base_url,
        model="nvidia/parakeet-ctc-1.1b",
        api_key=s.nebius_api_key,
    )
    try:
        text = await asr.transcribe(audio_bytes, language)
        return {"text": text, "adapter": asr.name, "language": language}
    except AudioTooLarge:
        raise HTTPException(413, "Audio clip too large.") from None
    except Exception as ex:
        raise HTTPException(502, f"ASR transcription service error: {str(ex)[:200]}") from ex


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
