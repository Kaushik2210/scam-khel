"""Per-tier token usage accounting (cost-tiering proof, exposed at /api/admin/usage)."""

from __future__ import annotations

import json
import statistics
import threading
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class UsageRecord:
    tier: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    request_id: str = "-"


@dataclass
class UsageTracker:
    records: list[UsageRecord] = field(default_factory=list)
    jsonl_path: Path | None = None
    sinks: list[Callable[[UsageRecord], None]] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def record(self, rec: UsageRecord) -> None:
        with self._lock:
            self.records.append(rec)
            if self.jsonl_path:
                self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
                with self.jsonl_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(asdict(rec)) + "\n")
        for sink in self.sinks:
            sink(rec)

    def total_tokens(self) -> int:
        return sum(r.prompt_tokens + r.completion_tokens for r in self.records)

    def summary(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for tier in ("fast", "mid", "deep"):
            rs = [r for r in self.records if r.tier == tier]
            lat = sorted(r.latency_ms for r in rs)
            out[tier] = {
                "calls": len(rs),
                "prompt_tokens": sum(r.prompt_tokens for r in rs),
                "completion_tokens": sum(r.completion_tokens for r in rs),
                "latency_p50_ms": round(statistics.median(lat), 1) if lat else None,
                "latency_p95_ms": round(lat[min(len(lat) - 1, int(len(lat) * 0.95))], 1)
                if lat
                else None,
                "models": sorted({r.model for r in rs}),
            }
        out["total_tokens"] = self.total_tokens()
        return out


tracker = UsageTracker()
