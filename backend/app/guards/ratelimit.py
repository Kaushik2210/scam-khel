"""Sliding-window rate limiter (in-memory; per-process, adequate for the single-container demo)."""

from __future__ import annotations

import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, clock=time.monotonic) -> None:  # type: ignore[no-untyped-def]
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._clock = clock

    def allow(self, key: str, limit: int, window_s: float) -> bool:
        now = self._clock()
        q = self._hits[key]
        while q and now - q[0] > window_s:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(now)
        return True

    def retry_after(self, key: str, window_s: float) -> int:
        q = self._hits.get(key)
        return max(1, int(window_s - (self._clock() - q[0]))) if q else 1

    def prune(self) -> None:
        for k in [k for k, q in self._hits.items() if not q]:
            del self._hits[k]
