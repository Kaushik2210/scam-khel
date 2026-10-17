"""Global daily token budget for the public demo."""

from __future__ import annotations

from datetime import UTC, date, datetime

from app.llm.usage import UsageRecord


class TokenBudget:
    def __init__(self, daily_limit: int, enforce: bool) -> None:
        self.daily_limit = daily_limit
        self.enforce = enforce
        self._day: date = datetime.now(UTC).date()
        self.used = 0
        self.forced_exhausted = False  # test / ops switch

    def _roll(self) -> None:
        today = datetime.now(UTC).date()
        if today != self._day:
            self._day, self.used, self.forced_exhausted = today, 0, False

    def record(self, rec: UsageRecord) -> None:
        self._roll()
        self.used += rec.prompt_tokens + rec.completion_tokens

    @property
    def exhausted(self) -> bool:
        self._roll()
        return self.enforce and (self.forced_exhausted or self.used >= self.daily_limit)

    def status(self) -> dict[str, object]:
        self._roll()
        return {
            "enforced": self.enforce,
            "daily_limit": self.daily_limit,
            "used": self.used,
            "remaining": max(0, self.daily_limit - self.used),
            "exhausted": self.exhausted,
            "resets": "00:00 UTC",
        }
