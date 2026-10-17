"""Replay sessions: served (clearly labelled) when the demo budget is exhausted."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPLAY_DIR = Path(__file__).resolve().parent.parent / "replays"


def list_replays() -> list[dict[str, Any]]:
    out = []
    for p in sorted(REPLAY_DIR.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        out.append(
            {
                "id": d["scenario"],
                "title": d.get("title", d["scenario"]),
                "source": d.get("source", "unknown"),
                "events": len(d["events"]),
            }
        )
    return out


def load_replay(scenario: str) -> dict[str, Any] | None:
    p = REPLAY_DIR / f"{scenario}.json"
    if not p.is_file() or p.parent != REPLAY_DIR:
        return None
    data: dict[str, Any] = json.loads(p.read_text(encoding="utf-8"))
    return data


def first_replay() -> dict[str, Any] | None:
    ps = sorted(REPLAY_DIR.glob("*.json"))
    return json.loads(ps[0].read_text(encoding="utf-8")) if ps else None
