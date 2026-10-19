from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.actions.telegram import TelegramClient
from app.api import routes_admin, routes_family, routes_memory, routes_sessions, ws
from app.api.state import AppState, new_fernet_key
from app.config import Settings, get_settings
from app.guards.budget import TokenBudget
from app.guards.ratelimit import RateLimiter
from app.llm.client import LLMClient
from app.llm.usage import UsageTracker
from app.logging import configure_logging, get_logger, new_request_id
from app.memory.crypto import Cipher
from app.memory.db import init_db, make_engine, make_sessionmaker
from app.memory.scripts import seed_scripts
from app.verify.tavily_verifier import TavilyVerifier

log = get_logger("app")
MAX_BODY = 64 * 1024

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), geolocation=(), microphone=(self)",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Cache-Control": "no-store",
}


class Guard(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        new_request_id()
        cl = request.headers.get("content-length")
        if cl and cl.isdigit() and int(cl) > MAX_BODY:
            return JSONResponse({"detail": "request too large"}, status_code=413)
        resp = await call_next(request)
        for k, v in SECURITY_HEADERS.items():
            resp.headers.setdefault(k, v)
        return resp


def _fernet_key(settings: Settings) -> str:
    if settings.fernet_key:
        return settings.fernet_key
    path = Path("data/.fernet_key")  # dev convenience; real deployments set FERNET_KEY
    if path.is_file():
        return path.read_text().strip()
    path.parent.mkdir(parents=True, exist_ok=True)
    key = new_fernet_key()
    path.write_text(key)
    log.warning("fernet_key_generated_locally", path=str(path))
    return key


def create_app(
    settings: Settings | None = None,
    llm: LLMClient | None = None,
    telegram: TelegramClient | None = None,
    verifier: TavilyVerifier | None = None,
    fernet_key: str | None = None,
    use_llm: bool | None = None,
) -> FastAPI:
    s = settings or get_settings()
    configure_logging()
    tracker = UsageTracker()
    budget = TokenBudget(s.daily_token_budget, enforce=s.demo_mode)
    tracker.sinks.append(budget.record)
    if llm is None:
        live_ok = bool(s.nebius_api_key and s.model_fast and s.model_mid) and not s.llm_offline
        if use_llm if use_llm is not None else live_ok:
            llm = LLMClient(s, tracker)
    elif llm.tracker is not tracker:
        llm.tracker = tracker
    engine = make_engine(s.database_url)
    state = AppState(
        settings=s,
        engine=engine,
        sm=make_sessionmaker(engine),
        cipher=Cipher(fernet_key or _fernet_key(s)),
        llm=llm,
        tracker=tracker,
        budget=budget,
        limiter=RateLimiter(),
        telegram=telegram or TelegramClient(s.telegram_bot_token),
        verifier=verifier or TavilyVerifier(s.tavily_api_key),
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if s.database_url.startswith("sqlite:///") or "sqlite+aiosqlite:///" in s.database_url:
            path = s.database_url.split("///", 1)[1]
            if path and path != ":memory:":
                Path(path).parent.mkdir(parents=True, exist_ok=True)
        await init_db(engine)
        async with state.sm() as db:
            await seed_scripts(db)
        await budget.load_from_db(state.sm)
        log.info("startup", llm_mode=state.llm_mode, demo=s.demo_mode, budget_used=budget.used)
        yield
        await engine.dispose()

    app = FastAPI(
        title="SCAM-KHEL", version="0.1.0", lifespan=lifespan, docs_url=None, redoc_url=None
    )
    app.state.s = state
    app.add_middleware(Guard)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[s.frontend_origin],
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "X-Client-Id", "X-Admin-Token"],
    )
    for r in (
        routes_admin.router,
        routes_sessions.router,
        routes_family.router,
        routes_memory.router,
        ws.router,
    ):
        app.include_router(r)

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled", error=type(exc).__name__)
        return JSONResponse({"detail": "internal error"}, status_code=500)

    return app
