from __future__ import annotations

from typing import Any

from sqlalchemy import event, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings
from app.memory.models import Base

FTS_DDL = (
    "CREATE VIRTUAL TABLE IF NOT EXISTS script_fts "
    "USING fts5(script_id UNINDEXED, name, phrases, tokenize='unicode61')"
)


def make_engine(url: str | None = None) -> AsyncEngine:
    url = url or get_settings().database_url
    engine = create_async_engine(url)
    if url.startswith("sqlite"):

        @event.listens_for(engine.sync_engine, "connect")
        def _pragmas(dbapi_conn: Any, _: Any) -> None:
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

    return engine


def make_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


def _create_all(conn: Connection) -> None:
    Base.metadata.create_all(conn)
    conn.execute(text(FTS_DDL))


async def init_db(engine: AsyncEngine) -> None:
    """Dev/test bootstrap. Production uses `alembic upgrade head` (same schema + FTS)."""
    async with engine.begin() as conn:
        await conn.run_sync(_create_all)
