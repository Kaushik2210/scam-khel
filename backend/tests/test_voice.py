import httpx
import pytest

from app.voice.asr import AudioTooLarge, HttpTranscriptionASR, voice_status
from app.voice.tts import HttpSpeechTTS


async def test_asr_posts_multipart_and_returns_text():
    seen = {}

    def handler(req: httpx.Request) -> httpx.Response:
        seen["url"] = str(req.url)
        seen["ct"] = req.headers["content-type"]
        return httpx.Response(200, json={"text": " namaste "})

    c = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    asr = HttpTranscriptionASR("https://asr.example.test/v1", "parakeet", http=c)
    assert await asr.transcribe(b"RIFF....", "hi-IN") == "namaste"
    assert seen["url"].endswith("/v1/audio/transcriptions") and "multipart" in seen["ct"]


async def test_asr_rejects_large_audio():
    with pytest.raises(AudioTooLarge):
        await HttpTranscriptionASR("https://x.test", "m").transcribe(b"0" * (3 * 1024 * 1024), "en")


async def test_tts_returns_bytes_and_truncates():
    def handler(req: httpx.Request) -> httpx.Response:
        assert len(req.read()) < 1000
        return httpx.Response(200, content=b"AUDIO")

    c = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    assert (
        await HttpSpeechTTS("https://t.example.test/v1", "magpie", http=c).synthesize(
            "x" * 5000, "hi"
        )
        == b"AUDIO"
    )


def test_status_is_honest_about_fallback():
    s = voice_status("", "")
    assert s["asr"]["active"] == "browser-web-speech" and s["asr"]["nvidia_verified"] is False
    assert s["audio_stored"] is False and "not an NVIDIA" in s["tts"]["fallback"]
    assert voice_status("https://a.test", "")["asr"]["active"] == "nvidia-asr-http"


def test_transcribe_endpoint_rejects_when_not_configured(tmp_path):
    from fastapi.testclient import TestClient

    from app.config import Settings
    from app.main import create_app

    app = create_app(Settings(_env_file=None, asr_base_url=""), use_llm=False)
    with TestClient(app) as client:
        r = client.post(
            "/api/voice/transcribe",
            content=b"RIFF1234",
            params={"language": "en"},
            headers={"Content-Type": "audio/wav"},
        )
        assert r.status_code == 501
        assert "not configured" in r.json()["detail"]


def test_transcribe_endpoint_rejects_empty_audio(tmp_path):
    from fastapi.testclient import TestClient

    from app.config import Settings
    from app.main import create_app

    app = create_app(Settings(_env_file=None, asr_base_url="https://asr.test/v1"), use_llm=False)
    with TestClient(app) as client:
        r = client.post("/api/voice/transcribe", content=b"")
        assert r.status_code == 400


def test_transcribe_endpoint_rejects_oversized_audio(tmp_path):
    from fastapi.testclient import TestClient

    from app.config import Settings
    from app.main import create_app

    app = create_app(Settings(_env_file=None, asr_base_url="https://asr.test/v1"), use_llm=False)
    with TestClient(app) as client:
        r = client.post(
            "/api/voice/transcribe",
            content=b"0" * (3 * 1024 * 1024),
            headers={"Content-Type": "audio/wav"},
        )
        assert r.status_code == 413

