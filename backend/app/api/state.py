from __future__ import annotations

import asyncio
import re
import secrets
import time
from dataclasses import dataclass, field
from typing import Any

from cryptography.fernet import Fernet
from fastapi import Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.actions.telegram import TelegramClient
from app.config import Settings
from app.guards.budget import TokenBudget
from app.guards.ratelimit import RateLimiter
from app.llm.client import LLMClient
from app.llm.usage import UsageTracker
from app.memory.crypto import Cipher
from app.memory.models import User
from app.verify.tavily_verifier import TavilyVerifier

CLIENT_ID_RE = re.compile(r"^[A-Za-z0-9\-]{8,64}$")
LIVE_TTL_S = 3600
MAX_LIVE = 50


@dataclass
class LiveSession:
    id: str
    user_id: int
    mode: str  # shield | honeypot | manual
    scenario: str
    language: str
    created: float = field(default_factory=time.time)
    stop: asyncio.Event = field(default_factory=asyncio.Event)
    inbox: asyncio.Queue[str | None] = field(default_factory=asyncio.Queue)
    started: bool = False
    summary: dict[str, Any] | None = None
    # Bearer for the websocket of this one session. It keeps the long-lived client ID
    # out of the websocket URL (and so out of access logs).
    ticket: str = field(default_factory=lambda: secrets.token_urlsafe(24))


@dataclass
class AppState:
    settings: Settings
    engine: AsyncEngine
    sm: async_sessionmaker[AsyncSession]
    cipher: Cipher
    llm: LLMClient | None
    tracker: UsageTracker
    budget: TokenBudget
    limiter: RateLimiter
    telegram: TelegramClient
    verifier: TavilyVerifier
    live: dict[str, LiveSession] = field(default_factory=dict)
    usage_flushed: int = 0

    def gc_live(self) -> None:
        now = time.time()
        for k in [k for k, v in self.live.items() if now - v.created > LIVE_TTL_S]:
            del self.live[k]

    @property
    def llm_mode(self) -> str:
        if self.llm is None:
            return "offline"
        return "nemotron-token-factory"


def new_fernet_key() -> str:
    return Fernet.generate_key().decode()


def get_state(request: Request) -> AppState:
    state: AppState = request.app.state.s
    return state


def client_ip(request: Request) -> str:
    """The caller's address for rate limiting.

    X-Forwarded-For is client-controlled unless a trusted proxy rewrote it, so it is only
    read when `trusted_proxy_hops` says how many proxies append to it. The entry that many
    hops from the right is the one our own outermost proxy saw; anything to its left is
    whatever the client claimed.
    """
    peer = request.client.host if request.client else "?"
    hops = get_state(request).settings.trusted_proxy_hops
    if hops > 0:
        parts = [p.strip() for p in request.headers.get("x-forwarded-for", "").split(",")]
        parts = [p for p in parts if p]
        if len(parts) >= hops:
            return parts[-hops]
    return peer


async def user_for_client(db: AsyncSession, client_id: str) -> User:
    if not CLIENT_ID_RE.match(client_id or ""):
        raise HTTPException(400, "missing or invalid X-Client-Id")
    u = await db.scalar(select(User).where(User.client_key == client_id))
    if u is None:
        u = User(client_key=client_id)
        db.add(u)
        await db.commit()
    return u


async def current_user(
    request: Request, x_client_id: str = Header(default="")
) -> tuple[AppState, User]:
    st = get_state(request)
    async with st.sm() as db:
        u = await user_for_client(db, x_client_id)
    return st, u
