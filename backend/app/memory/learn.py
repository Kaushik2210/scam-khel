"""Post-session learning: fingerprint the observed script and upsert it into the library."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.detect.taxonomy import is_valid_tactic
from app.memory.models import Incident, ScamScript
from app.memory.retrieval import (
    first_appearance_sequence,
    fts_upsert,
    full_similarity,
    normalise_phrase,
)

MERGE_THRESHOLD = 0.75
MAX_PHRASES = 40


@dataclass
class LearnTurn:
    speaker: str
    tactics: list[str] = field(default_factory=list)
    evidence_spans: list[str] = field(default_factory=list)


async def learn_session(
    db: AsyncSession,
    *,
    session_id: str,
    turns: list[LearnTurn],
    detect_turn: int | None,
    summary: str = "",
    memory_hit_turn: int | None = None,
) -> Incident:
    """Create the Incident, then merge into (or create) a ScamScript."""
    scammer = [t for t in turns if t.speaker == "scammer"]
    seq = [
        t
        for t in first_appearance_sequence(
            [[x for x in tu.tactics if is_valid_tactic(x)] for tu in scammer]
        )
    ]
    phrases = list(
        dict.fromkeys(
            p for tu in scammer for sp in tu.evidence_spans if (p := normalise_phrase(sp))
        )
    )

    incident = Incident(
        session_id=session_id,
        summary=summary,
        detect_turn=detect_turn,
        memory_hit_turn=memory_hit_turn,
    )
    db.add(incident)
    await db.flush()
    if len(seq) < 2:  # too little signal to fingerprint
        await db.commit()
        return incident

    match: ScamScript | None = None
    best = 0.0
    for s in (await db.scalars(select(ScamScript))).all():
        sim = full_similarity(seq, s.tactic_sequence)
        if sim >= MERGE_THRESHOLD and sim > best:
            match, best = s, sim

    now = datetime.now(UTC)
    if match is None:
        n = len((await db.scalars(select(ScamScript.id))).all()) + 1
        match = ScamScript(
            name=f"learned-{n}",
            tactic_sequence=seq,
            phrases=phrases[:MAX_PHRASES],
            seen_count=1,
            first_incident_id=incident.id,
        )
        db.add(match)
        await db.flush()
    else:
        match.seen_count += 1
        match.last_seen = now
        if (
            len(seq) > len(match.tactic_sequence)
            and full_similarity(match.tactic_sequence, seq) >= MERGE_THRESHOLD
        ):
            match.tactic_sequence = seq  # observed a longer variant of the same script
        match.phrases = list(dict.fromkeys([*match.phrases, *phrases]))[:MAX_PHRASES]
        if match.first_incident_id is None:
            match.first_incident_id = incident.id
    incident.recognised_script_id = match.id
    await fts_upsert(db, match)
    await db.commit()
    return incident
