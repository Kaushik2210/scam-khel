from __future__ import annotations

import asyncio
import ipaddress
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


def _parse_trusted_proxies(trusted_str: str) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    nets: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
    for item in trusted_str.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            if "/" in item:
                nets.append(ipaddress.ip_network(item, strict=False))
            else:
                ip = ipaddress.ip_address(item)
                nets.append(ipaddress.ip_network(f"{ip}/{32 if ip.version == 4 else 128}"))
        except ValueError:
            continue
    return nets


def _is_ip_trusted(ip_str: str, nets: list[ipaddress.IPv4Network | ipaddress.IPv6Network]) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str.strip())
        return any(ip in net for net in nets)
    except ValueError:
        return False


def client_ip(request: Request, trusted_proxies: str | None = None) -> str:
    """Return the client's IP address.

    If trusted_proxies is configured, parse X-Forwarded-For right-to-left
    skipping trusted proxies to find the rightmost untrusted hop.
    If direct client is not trusted or trusted_proxies is empty,
    X-Forwarded-For is ignored to prevent spoofing.
    """
    direct = request.client.host if request.client else "?"
    if trusted_proxies is None:
        try:
            trusted_proxies = request.app.state.s.settings.trusted_proxies
        except AttributeError:
            trusted_proxies = ""

    trusted_nets = _parse_trusted_proxies(trusted_proxies)
    if not trusted_nets:
        return direct

    if direct != "?" and not _is_ip_trusted(direct, trusted_nets):
        return direct

    fwd = request.headers.get("x-forwarded-for", "")
    if not fwd:
        return direct

    hops = [h.strip() for h in fwd.split(",") if h.strip()]
    for hop in reversed(hops):
        if not _is_ip_trusted(hop, trusted_nets):
            return hop
    return hops[0] if hops else direct


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
