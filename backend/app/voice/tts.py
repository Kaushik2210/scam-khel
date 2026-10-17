"""TTS adapters (mirror of asr.py). NVIDIA Magpie TTS via an HTTP endpoint when configured
(`TTS_BASE_URL`, UNVERIFIED here); otherwise the browser's speechSynthesis is used client-side."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx

MAX_TEXT = 600


class TTS(Protocol):
    name: str
    nvidia: bool

    async def synthesize(self, text: str, language: str) -> bytes: ...


@dataclass
class HttpSpeechTTS:
    base_url: str
    model: str
    voice: str = "default"
    api_key: str = ""
    name: str = "nvidia-tts-http"
    nvidia: bool = True
    http: httpx.AsyncClient | None = None

    async def synthesize(self, text: str, language: str) -> bytes:
        client = self.http or httpx.AsyncClient(timeout=30)
        try:
            r = await client.post(
                f"{self.base_url.rstrip('/')}/audio/speech",
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                json={
                    "model": self.model,
                    "input": text[:MAX_TEXT],
                    "voice": self.voice,
                    "language": language[:2],
                },
            )
            r.raise_for_status()
            return r.content
        finally:
            if self.http is None:
                await client.aclose()
