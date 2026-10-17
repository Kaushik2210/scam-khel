"""ASR adapters. Text mode never depends on any of this.

Paths (record the one used in the demo in DECISIONS.md):
  1. NVIDIA speech model (Parakeet / Nemotron-speech) behind an OpenAI-compatible
     `/v1/audio/transcriptions` endpoint (`ASR_BASE_URL`). UNVERIFIED in this build: no endpoint
     was available to test against.
  2. Fallback: the browser Web Speech API (hi-IN / en-IN). Not an NVIDIA model.
Audio is transcribed and discarded; it is never written to disk or the database.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import httpx

MAX_AUDIO_BYTES = 2 * 1024 * 1024


class ASR(Protocol):
    name: str
    nvidia: bool

    async def transcribe(self, audio: bytes, language: str) -> str: ...


class AudioTooLarge(ValueError):
    pass


@dataclass
class HttpTranscriptionASR:
    base_url: str
    model: str
    api_key: str = ""
    name: str = "nvidia-asr-http"
    nvidia: bool = True
    http: httpx.AsyncClient | None = None

    async def transcribe(self, audio: bytes, language: str) -> str:
        if len(audio) > MAX_AUDIO_BYTES:
            raise AudioTooLarge("audio clip too large")
        client = self.http or httpx.AsyncClient(timeout=30)
        try:
            r = await client.post(
                f"{self.base_url.rstrip('/')}/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                data={"model": self.model, "language": language[:2]},
                files={"file": ("clip.wav", audio, "audio/wav")},
            )
            r.raise_for_status()
            data: dict[str, Any] = r.json()
            return str(data.get("text", "")).strip()
        finally:
            if self.http is None:
                await client.aclose()


def voice_status(asr_base_url: str, tts_base_url: str) -> dict[str, Any]:
    return {
        "asr": {
            "active": "nvidia-asr-http" if asr_base_url else "browser-web-speech",
            "nvidia_configured": bool(asr_base_url),
            "nvidia_verified": False,
            "fallback": "Browser Web Speech API (hi-IN, en-IN): not an NVIDIA model",
        },
        "tts": {
            "active": "nvidia-tts-http" if tts_base_url else "browser-speech-synthesis",
            "nvidia_configured": bool(tts_base_url),
            "nvidia_verified": False,
            "fallback": "Browser speechSynthesis: not an NVIDIA model",
        },
        "audio_stored": False,
        "note": "The NVIDIA-model requirement is met by Nemotron on Token Factory, not by voice.",
    }
