"""Tavily runtime verification: official advisories, claim checks, best-effort report search.

"No public reports found" is NOT evidence of safety; results are labelled accordingly.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol

from app.logging import get_logger

log = get_logger("tavily")

OFFICIAL_DOMAINS = [
    "cybercrime.gov.in",
    "pib.gov.in",
    "mha.gov.in",
    "rbi.org.in",
    "i4c.mha.gov.in",
    "sancharsaathi.gov.in",
    "trai.gov.in",
]
NEWS_DOMAINS = ["thehindu.com", "indianexpress.com", "timesofindia.indiatimes.com", "ndtv.com"]
CACHE_TTL_S = 6 * 3600
NO_REPORTS_NOTE = (
    "No public reports found. This does NOT mean it is safe: new scam numbers and accounts "
    "are often not yet reported."
)


class SearchClient(Protocol):
    async def search(self, query: str, **kwargs: Any) -> dict[str, Any]: ...


@dataclass
class Source:
    title: str
    url: str
    snippet: str


@dataclass
class Verification:
    kind: str  # advisory | claim_check | report_search
    query: str
    status: str  # ok | no_results | unavailable
    sources: list[Source] = field(default_factory=list)
    note: str = ""
    cached: bool = False
    provider: str = "tavily"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sources(resp: dict[str, Any]) -> list[Source]:
    return [
        Source(r.get("title", ""), r.get("url", ""), (r.get("content") or "")[:300])
        for r in resp.get("results", [])
        if r.get("url")
    ]


class TavilyVerifier:
    def __init__(self, api_key: str = "", client: SearchClient | None = None, max_calls: int = 6):
        self._client = client
        self._api_key = api_key
        self.max_calls = max_calls
        self.calls = 0
        self._cache: dict[tuple[str, str, bool], tuple[float, Verification]] = {}

    @property
    def available(self) -> bool:
        return self._client is not None or bool(self._api_key)

    def _get_client(self) -> SearchClient:
        if self._client is None:
            from tavily import AsyncTavilyClient

            self._client = AsyncTavilyClient(api_key=self._api_key)
        assert self._client is not None
        return self._client

    async def _run(self, kind: str, query: str, official_only: bool, **kw: Any) -> Verification:
        key = (kind, query.lower(), official_only)
        hit = self._cache.get(key)
        if hit and time.time() - hit[0] < CACHE_TTL_S:
            v = Verification(**{**asdict(hit[1]), "cached": True, "sources": hit[1].sources})
            return v
        if not self.available:
            return Verification(kind, query, "unavailable", note="Tavily API key not configured.")
        if self.calls >= self.max_calls:
            return Verification(kind, query, "unavailable", note="Verification budget reached.")
        self.calls += 1
        try:
            resp = await self._get_client().search(
                query,
                max_results=4,
                search_depth="basic",
                include_domains=OFFICIAL_DOMAINS if official_only else None,
                **kw,
            )
        except Exception as e:  # quota, auth, network: degrade gracefully
            log.warning("tavily_unavailable", error=type(e).__name__)
            return Verification(
                kind,
                query,
                "unavailable",
                note=f"Verification service unavailable ({type(e).__name__}); not a safety signal.",
            )
        srcs = _sources(resp)
        v = Verification(
            kind,
            query,
            "ok" if srcs else "no_results",
            srcs,
            "" if srcs else NO_REPORTS_NOTE,
        )
        self._cache[key] = (time.time(), v)
        return v

    async def fetch_advisory(self) -> Verification:
        """Ground the 'what to do' copy in current official advisory text."""
        return await self._run(
            "advisory",
            "digital arrest scam advisory police CBI do not arrest on video call",
            official_only=True,
        )

    async def check_claim(self, claim: str) -> Verification:
        """Check a claimed agency / officer / case against official sources."""
        return await self._run("claim_check", f"{claim} official advisory fake", official_only=True)

    async def search_reports(self, identifier: str) -> Verification:
        """Best-effort public reports for a number / UPI id (general web + news)."""
        return await self._run(
            "report_search", f'"{identifier}" scam fraud reported', official_only=False
        )
