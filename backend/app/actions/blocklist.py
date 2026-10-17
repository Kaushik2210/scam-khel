"""Blocklist export: extracted identifiers for the user to share with their bank/telecom."""

from __future__ import annotations

import csv
import io
import json
from datetime import UTC, datetime
from typing import Any

BLOCKABLE = ["phone", "upi", "account", "ifsc", "url", "apk"]


def _rows(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    rows = []
    for e in evidence:
        if e["type"] not in BLOCKABLE:
            continue
        k = (e["type"], str(e["value"]).lower())
        if k in seen:
            continue
        seen.add(k)
        rows.append(
            {
                "type": e["type"],
                "value": e["value"],
                "confidence": e.get("confidence", 0),
                "mentions": e.get("mentions", 1),
            }
        )
    return rows


def to_csv(evidence: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["type", "value", "confidence", "mentions"])
    w.writeheader()
    for r in _rows(evidence):
        # neutralise spreadsheet formula injection from attacker-controlled values
        r["value"] = "'" + r["value"] if str(r["value"])[:1] in "=+-@" else r["value"]
        w.writerow(r)
    return buf.getvalue()


def to_json(evidence: list[dict[str, Any]], simulation: bool = False) -> str:
    return json.dumps(
        {
            "generated": datetime.now(UTC).isoformat(timespec="seconds"),
            "simulation": simulation,
            "note": "Reported/extracted identifiers; verify before blocking.",
            "items": _rows(evidence),
        },
        indent=2,
        ensure_ascii=False,
    )
