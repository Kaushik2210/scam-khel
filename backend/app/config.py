from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

Tier = Literal["fast", "mid", "deep"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    nebius_api_key: str = ""
    nebius_base_url: str = "https://api.tokenfactory.us-central1.nebius.com/v1/"
    model_fast: str = ""
    model_mid: str = ""
    model_deep: str = ""
    structured_mode: Literal["auto", "json_prompt", "tools"] = "json_prompt"
    llm_timeout_s: float = 60.0
    llm_max_retries: int = 4
    llm_offline: bool = False

    tavily_api_key: str = ""
    telegram_bot_token: str = ""
    fernet_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./data/scamkhel.db"
    retention_days: int = 30

    asr_base_url: str = (
        ""  # optional NVIDIA ASR endpoint (OpenAI-compatible); unset = browser fallback
    )
    tts_base_url: str = ""
    demo_mode: bool = False
    daily_token_budget: int = 500_000
    per_ip_sessions_per_hour: int = 6
    max_turns_per_session: int = 20
    admin_token: str = ""
    frontend_origin: str = "http://localhost:3000"

    def model_for(self, tier: Tier) -> str:
        return {"fast": self.model_fast, "mid": self.model_mid, "deep": self.model_deep}[tier]


@lru_cache
def get_settings() -> Settings:
    return Settings()
