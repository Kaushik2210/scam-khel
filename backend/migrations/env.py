from alembic import context
from sqlalchemy import create_engine

from app.config import get_settings
from app.memory.models import Base

target_metadata = Base.metadata


def _sync_url() -> str:
    return get_settings().database_url.replace("+aiosqlite", "").replace("+asyncpg", "")


def run_migrations_online() -> None:
    engine = create_engine(_sync_url())
    with engine.connect() as conn:
        context.configure(connection=conn, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
