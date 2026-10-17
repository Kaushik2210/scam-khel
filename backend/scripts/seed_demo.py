"""Seed the demo DB so the memory-hit moment is reproducible on camera.

Creates two prior incidents (offline, deterministic) for the demo client so that on camera a
second, similar run is "Recognised pattern from Incident #N - flagged at turn k vs turn m earlier".
Open the app once with ?client=demo-client-0001 to see these incidents under Incidents.

Usage: python scripts/seed_demo.py [--reset]
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from sqlalchemy import select

from app.config import get_settings
from app.main import _fernet_key
from app.memory import repo
from app.memory.crypto import Cipher
from app.memory.db import init_db, make_engine, make_sessionmaker
from app.memory.models import User
from app.memory.scripts import seed_scripts
from app.orchestrator import Orchestrator

DEMO_CLIENT = "demo-client-0001"
SEED_SCENARIOS = ["digital-arrest-parcel", "kyc-expiry-bank"]


async def main(reset: bool) -> None:
    s = get_settings()
    if reset and s.database_url.startswith("sqlite"):
        path = Path(s.database_url.split("///", 1)[1])
        for suffix in ("", "-wal", "-shm"):
            Path(str(path) + suffix).unlink(missing_ok=True)
    engine = make_engine(s.database_url)
    await init_db(engine)
    cipher = Cipher(_fernet_key(s))
    async with make_sessionmaker(engine)() as db:
        await seed_scripts(db)
        user = await db.scalar(select(User).where(User.client_key == DEMO_CLIENT))
        if user is None:
            user = User(client_key=DEMO_CLIENT)
            db.add(user)
            await db.commit()
        await repo.record_consent(db, user.id)
        for sc in SEED_SCENARIOS:
            sm = await Orchestrator(db=db, cipher=cipher, user_id=user.id, seed=1).run(
                sc, "honeypot", 10
            )
            print(
                f"seeded incident #{sm.incident_id} ({sc}): peak {sm.risk_peak}, detect turn {sm.detect_turn}"
            )
    await engine.dispose()
    print(f"Done. Demo client id: {DEMO_CLIENT}  (open the app with ?client={DEMO_CLIENT})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true", help="delete the SQLite file first")
    asyncio.run(main(ap.parse_args().reset))
