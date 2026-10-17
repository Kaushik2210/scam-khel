"""Shield mode: incremental analysis of a pasted/spoken/streamed transcript (no persona)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.detect.risk import CAUTION, HIGH, RiskEngine, active_tactics, explain
from app.detect.tagger import guess_language, tag_utterance
from app.evidence.extractor import EvidenceStore
from app.llm.client import LLMClient
from app.memory import repo
from app.memory.crypto import Cipher
from app.memory.learn import LearnTurn, learn_session
from app.memory.models import EvidenceItem, Session
from app.memory.retrieval import first_appearance_sequence, recognize
from app.orchestrator import AlertHook, Emit, _noop_emit


@dataclass
class ShieldResult:
    score: int = 0
    level: str = "low"
    stage: str = "contact"
    tactics: list[str] = field(default_factory=list)
    explanation: dict[str, object] = field(default_factory=dict)
    evidence: list[dict[str, object]] = field(default_factory=list)
    detect_turn: int | None = None
    turns: int = 0
    transcript: list[dict[str, Any]] = field(default_factory=list)
    timeline: list[dict[str, Any]] = field(default_factory=list)
    memory_hit: dict[str, Any] | None = None
    incident_id: int | None = None


class ShieldAnalyzer:
    def __init__(
        self,
        llm: LLMClient | None = None,
        emit: Emit | None = None,
        alert_hook: AlertHook | None = None,
        session_id: str = "",
        db: AsyncSession | None = None,
        cipher: Cipher | None = None,
        user_id: int | None = None,
        language: str = "en",
    ) -> None:
        self.db, self.cipher, self.user_id, self.language = db, cipher, user_id, language
        self.turn_tactics: list[list[str]] = []
        self.learn_turns: list[LearnTurn] = []
        self.llm, self.emit, self.alert_hook = llm, emit or _noop_emit, alert_hook
        self.sid = session_id
        self.risk = RiskEngine()
        self.store = EvidenceStore()
        self.res = ShieldResult()
        self._alerted: set[str] = set()

    async def feed(self, text: str, speaker: str = "caller") -> ShieldResult:
        """Feed one utterance. Only the other party's ('caller') text is scored."""
        r = self.res
        r.turns += 1
        n = r.turns
        r.transcript.append(
            {"turn": n, "speaker": "scammer" if speaker == "caller" else "victim", "text": text}
        )
        await self.emit("transcript", {"turn": n, "speaker": speaker, "text": text})
        if speaker != "caller":
            return r
        tagged = await tag_utterance(text, self.llm)
        st = self.risk.update(tagged)
        self.turn_tactics.append([t.id for t in tagged.tactics if t.confidence >= 0.5])
        self.learn_turns.append(
            LearnTurn(
                "scammer",
                self.turn_tactics[-1],
                [
                    t.evidence_span
                    for t in tagged.tactics
                    if t.confidence >= 0.5 and t.evidence_span
                ],
            )
        )
        if self.db is not None and r.memory_hit is None:
            hit = await recognize(
                self.db,
                first_appearance_sequence(self.turn_tactics),
                " ".join(t["text"] for t in r.transcript if t["speaker"] == "scammer"),
                n,
            )
            if hit:
                st = self.risk.apply_memory_prior(HIGH if hit.seen_count >= 1 else CAUTION + 15)
                r.memory_hit = {
                    "script": hit.script_name,
                    "banner": hit.banner(),
                    "hit_turn": n,
                    "earlier_incident_id": hit.earlier_incident_id,
                    "earlier_detect_turn": hit.earlier_detect_turn,
                    "seen_count": hit.seen_count,
                }
                await self.emit("memory_hit", r.memory_hit)
        r.score, r.level, r.stage = st.score, st.level, st.stage
        r.tactics = [t.id for t in active_tactics(st)]
        r.explanation = explain(st, guess_language(text))
        if r.detect_turn is None and st.score >= HIGH:
            r.detect_turn = n
        r.timeline.append({"turn": n, "stage": st.stage, "tactics": r.tactics, "risk": st.score})
        await self.emit(
            "tactics",
            {
                "turn": n,
                "tactics": [t.model_dump() for t in tagged.tactics],
                "stage": tagged.stage,
                "injection": tagged.injection_flagged,
            },
        )
        await self.emit(
            "risk", {"turn": n, **r.explanation, "stage": st.stage, "active_tactics": r.tactics}
        )
        for rec in await self.store.ingest(text, n, self.llm):
            await self.emit("evidence", {"item": rec.as_dict()})
        r.evidence = [e.as_dict() for e in self.store.items()]
        if self.alert_hook and st.level in ("high", "critical") and st.level not in self._alerted:
            self._alerted.add(st.level)
            await self.alert_hook(
                st.level,
                {
                    "session_id": self.sid,
                    "turn": n,
                    "score": st.score,
                    "tactics": r.tactics,
                    "scenario": "shield",
                },
            )
        return r

    async def finish(self) -> ShieldResult:
        """Persist session, encrypted transcript, evidence; learn the script."""
        r = self.res
        if self.db is None or self.user_id is None or self.cipher is None or not self.sid:
            return r
        self.db.add(
            Session(
                id=self.sid,
                user_id=self.user_id,
                mode="shield",
                language=self.language,
                risk_peak=r.score,
                ended_at=datetime.now(UTC),
            )
        )
        await self.db.flush()
        for t in r.transcript:
            await repo.add_utterance(
                self.db,
                self.cipher,
                session_id=self.sid,
                turn=t["turn"],
                speaker=t["speaker"],
                text_plain=t["text"],
            )
        for e in self.store.items():
            self.db.add(
                EvidenceItem(
                    session_id=self.sid, type=e.type, value=e.value, confidence=e.confidence
                )
            )
        inc = await learn_session(
            self.db,
            session_id=self.sid,
            turns=self.learn_turns,
            detect_turn=r.detect_turn,
            summary=f"shield: peak risk {r.score}, {len(r.evidence)} identifiers",
            memory_hit_turn=(r.memory_hit or {}).get("hit_turn"),
        )
        inc.data = {
            "scenario": "shield",
            "timeline": r.timeline,
            "verifications": [],
            "risk_peak": r.score,
            "time_wasted_s": 0,
            "simulation": False,
        }
        r.incident_id = inc.id
        await self.db.commit()
        return r
