"""Script retrieval: tactic-sequence similarity + FTS5 phrase search + memory-hit recognition."""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.models import Incident, ScamScript

MATCH_THRESHOLD = 0.8


def normalise_phrase(s: str) -> str:
    s = s.lower()
    s = re.sub(r"\d+", "<num>", s)
    s = re.sub(r"[^\w<>\s]", " ", s, flags=re.UNICODE)
    return re.sub(r"\s+", " ", s).strip()


def first_appearance_sequence(turns: list[list[str]]) -> list[str]:
    """Flatten per-turn tactic lists into order-of-first-appearance."""
    seen: list[str] = []
    for tactics in turns:
        for t in tactics:
            if t not in seen:
                seen.append(t)
    return seen


def lcs_len(a: list[str], b: list[str]) -> int:
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b, 1):
            cur.append(prev[j - 1] + 1 if x == y else max(prev[j], cur[j - 1]))
        prev = cur
    return prev[-1]


def prefix_score(observed: list[str], script: list[str]) -> float:
    """How much of what we've seen so far follows the script (order-aware)."""
    return lcs_len(observed, script) / len(observed) if observed else 0.0


def full_similarity(a: list[str], b: list[str]) -> float:
    """Symmetric similarity used when deciding whether two finished sessions are one script."""
    return lcs_len(a, b) / max(len(a), len(b)) if a and b else 0.0


def min_prefix_len(seen_count: int) -> int:
    """Learned priors: scripts seen repeatedly are recognised from a shorter prefix."""
    return 3 if seen_count < 2 else 2


def _fts_query(text_in: str) -> str:
    words = [w for w in normalise_phrase(text_in).split() if len(w) > 2 and w != "<num>"]
    return " OR ".join(f'"{w}"' for w in dict.fromkeys(words))


async def fts_upsert(db: AsyncSession, s: ScamScript) -> None:
    await db.execute(text("DELETE FROM script_fts WHERE script_id = :i"), {"i": s.id})
    await db.execute(
        text("INSERT INTO script_fts(script_id, name, phrases) VALUES (:i, :n, :p)"),
        {"i": s.id, "n": s.name.replace("-", " "), "p": " . ".join(s.phrases)},
    )


async def fts_scores(db: AsyncSession, query_text: str, limit: int = 10) -> dict[int, float]:
    """Return script_id -> relevance in (0, 1] (best hit = 1)."""
    q = _fts_query(query_text)
    if not q:
        return {}
    rows = (
        await db.execute(
            text(
                "SELECT script_id, bm25(script_fts) AS r FROM script_fts "
                "WHERE script_fts MATCH :q ORDER BY r LIMIT :n"
            ),
            {"q": q, "n": limit},
        )
    ).all()
    if not rows:
        return {}
    worst = max(abs(float(r.r)) for r in rows) or 1.0
    return {int(r.script_id): abs(float(r.r)) / worst for r in rows}


@dataclass(frozen=True)
class MemoryHit:
    script_id: int
    script_name: str
    score: float
    seen_count: int
    earlier_incident_id: int | None
    earlier_detect_turn: int | None
    hit_turn: int | None = None

    def banner(self) -> str:
        if self.earlier_incident_id is None:
            return f"Recognised known script pattern '{self.script_name}'."
        msg = f"Recognised pattern from Incident #{self.earlier_incident_id}"
        if self.hit_turn is not None and self.earlier_detect_turn is not None:
            msg += f" — flagged at turn {self.hit_turn} vs turn {self.earlier_detect_turn} earlier"
        return msg


async def recognize(
    db: AsyncSession, observed: list[str], text_so_far: str = "", hit_turn: int | None = None
) -> MemoryHit | None:
    """Return the best known script matching the tactic prefix seen so far, else None."""
    if not observed:
        return None
    scripts = (await db.scalars(select(ScamScript))).all()
    fts = await fts_scores(db, text_so_far) if text_so_far else {}
    best: tuple[float, ScamScript] | None = None
    for s in scripts:
        if len(observed) < min_prefix_len(s.seen_count):
            continue
        sc = prefix_score(observed, s.tactic_sequence)
        if sc < MATCH_THRESHOLD:
            continue
        rank = sc + 0.15 * fts.get(s.id, 0.0) + 0.02 * min(s.seen_count, 5)
        if best is None or rank > best[0]:
            best = (rank, s)
    if best is None:
        return None
    s = best[1]
    inc = await db.get(Incident, s.first_incident_id) if s.first_incident_id else None
    return MemoryHit(
        script_id=s.id,
        script_name=s.name,
        score=round(prefix_score(observed, s.tactic_sequence), 3),
        seen_count=s.seen_count,
        earlier_incident_id=inc.id if inc else None,
        earlier_detect_turn=inc.detect_turn if inc else None,
        hit_turn=hit_turn,
    )
