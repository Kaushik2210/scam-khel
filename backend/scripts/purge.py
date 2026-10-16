"""Retention purge (cron-able): deletes sessions older than RETENTION_DAYS.

Usage: python scripts/purge.py [--days N]
"""

from __future__ import annotations

import argparse
import asyncio

from app.config import get_settings
from app.memory import repo
from app.memory.db import make_engine, make_sessionmaker


async def main(days: int) -> int:
    engine = make_engine()
    async with make_sessionmaker(engine)() as db:
        n = await repo.purge_older_than(db, days)
    await engine.dispose()
    print(f"purged {n} session(s) older than {days} day(s)")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=get_settings().retention_days)
    raise SystemExit(asyncio.run(main(ap.parse_args().days)))
