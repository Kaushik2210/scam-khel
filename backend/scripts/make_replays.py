"""Record replay sessions served when the demo token budget is exhausted.

Offline (default): records the deterministic rules+scripted run, labelled 'offline-scripted'.
Live: `python scripts/make_replays.py --live` records real Nemotron runs ('live-nemotron').
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.llm.client import LLMClient
from app.orchestrator import Orchestrator
from app.simulator.scenario import load_scenario

OUT = Path(__file__).resolve().parents[1] / "app" / "replays"
SCENARIOS = ["digital-arrest-parcel", "kyc-expiry-bank", "fake-police-family-accident"]


async def record(scenario: str, live: bool) -> dict[str, Any]:
    events: list[dict[str, Any]] = []

    async def emit(t: str, p: dict[str, Any]) -> None:
        events.append({"type": t, **p})

    llm = LLMClient(get_settings()) if live else None
    sm = await Orchestrator(llm=llm, emit=emit, seed=7).run(scenario, "honeypot", max_turns=10)
    return {
        "scenario": scenario,
        "title": load_scenario(scenario).title,
        "source": "live-nemotron" if live else "offline-scripted",
        "summary": {"risk_peak": sm.risk_peak, "time_wasted_s": sm.time_wasted_s},
        "events": events,
    }


async def main(live: bool) -> None:
    OUT.mkdir(exist_ok=True)
    for sc in SCENARIOS:
        data = await record(sc, live)
        (OUT / f"{sc}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"wrote {sc}: {len(data['events'])} events ({data['source']})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    asyncio.run(main(ap.parse_args().live))
