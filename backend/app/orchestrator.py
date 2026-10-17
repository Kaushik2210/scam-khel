"""Session orchestration: scammer sim -> detector -> risk -> memory -> evidence -> persona."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.detect.risk import CAUTION, HIGH, RiskEngine, active_tactics, explain
from app.detect.tagger import guess_language, tag_utterance
from app.evidence.extractor import EvidenceStore
from app.llm.client import LLMClient
from app.logging import get_logger
from app.memory import repo
from app.memory.crypto import Cipher
from app.memory.learn import LearnTurn, learn_session
from app.memory.models import EvidenceItem, Incident, Session
from app.memory.retrieval import MemoryHit, first_appearance_sequence, recognize
from app.persona.persona import Persona, PersonaConfig
from app.simulator.scammer import ScammerSim
from app.simulator.scenario import load_scenario

log = get_logger("orchestrator")

Emit = Callable[[str, dict[str, Any]], Awaitable[None]]
AlertHook = Callable[[str, dict[str, Any]], Awaitable[None]]
VictimProvider = Callable[[], Awaitable[str | None]]


async def _noop_emit(_: str, __: dict[str, Any]) -> None:
    return None


@dataclass
class SessionSummary:
    session_id: str
    scenario: str
    mode: str
    scammer_turns: int = 0
    persona_turns: int = 0
    risk_peak: int = 0
    level: str = "low"
    detect_turn: int | None = None  # first scammer turn with risk >= high
    critical_turn: int | None = None
    time_wasted_s: int = 0
    guarded_outputs: int = 0
    injection_attempts: int = 0
    memory_hit: dict[str, Any] | None = None
    incident_id: int | None = None
    evidence: list[dict[str, object]] = field(default_factory=list)
    ended_reason: str = "completed"
    transcript: list[dict[str, Any]] = field(default_factory=list)


class Orchestrator:
    def __init__(
        self,
        llm: LLMClient | None = None,
        db: AsyncSession | None = None,
        cipher: Cipher | None = None,
        emit: Emit | None = None,
        alert_hook: AlertHook | None = None,
        user_id: int | None = None,
        seed: int = 0,
        persona_config: PersonaConfig | None = None,
    ) -> None:
        self.llm, self.db, self.cipher = llm, db, cipher
        self.emit = emit or _noop_emit
        self.alert_hook = alert_hook
        self.user_id = user_id
        self.seed = seed
        self.persona_config = persona_config

    async def run(
        self,
        scenario_id: str,
        mode: str = "honeypot",
        max_turns: int = 12,
        victim_provider: VictimProvider | None = None,
        stop: asyncio.Event | None = None,
        pace_s: float = 0.0,
    ) -> SessionSummary:
        sc = load_scenario(scenario_id)
        sim = ScammerSim(sc, self.llm, self.seed)
        persona = Persona(self.llm, self.persona_config, self.seed)
        risk = RiskEngine()
        store = EvidenceStore()
        sid = str(uuid.uuid4())
        sm = SessionSummary(session_id=sid, scenario=scenario_id, mode=mode)
        history: list[tuple[str, str]] = []
        turn_tactics: list[list[str]] = []
        learn_turns: list[LearnTurn] = []
        alerted: set[str] = set()

        if self.db is not None and self.user_id is not None:
            self.db.add(
                Session(
                    id=sid,
                    user_id=self.user_id,
                    mode=mode,
                    scenario=scenario_id,
                    language=sc.language,
                )
            )
            await self.db.flush()

        for n in range(1, max_turns + 1):
            if stop is not None and stop.is_set():
                sm.ended_reason = "user_takeover"
                break
            turn = await sim.next_line(history)
            history.append(("scammer", turn.text))
            sm.scammer_turns = n
            sm.transcript.append(
                {"turn": n, "speaker": "scammer", "text": turn.text, "stage": turn.stage}
            )
            await self.emit(
                "transcript",
                {"turn": n, "speaker": "scammer", "text": turn.text, "simulation": True},
            )

            tagged = await tag_utterance(turn.text, self.llm)
            if tagged.injection_flagged:
                sm.injection_attempts += 1
            st = risk.update(tagged)
            turn_tactics.append([t.id for t in tagged.tactics if t.confidence >= 0.5])
            if self.db is not None and sm.memory_hit is None:
                seq = first_appearance_sequence(turn_tactics)
                hit: MemoryHit | None = await recognize(
                    self.db, seq, " ".join(t for s_, t in history if s_ == "scammer"), n
                )
                if hit:
                    # learned priors: a script seen before is treated as high risk immediately
                    st = risk.apply_memory_prior(HIGH if hit.seen_count >= 1 else CAUTION + 15)
                    sm.memory_hit = {
                        "script": hit.script_name,
                        "banner": hit.banner(),
                        "hit_turn": n,
                        "earlier_incident_id": hit.earlier_incident_id,
                        "earlier_detect_turn": hit.earlier_detect_turn,
                        "seen_count": hit.seen_count,
                    }
                    await self.emit("memory_hit", sm.memory_hit)
            active = [t.id for t in active_tactics(st)]
            learn_turns.append(
                LearnTurn(
                    "scammer",
                    turn_tactics[-1],
                    [
                        t.evidence_span
                        for t in tagged.tactics
                        if t.confidence >= 0.5 and t.evidence_span
                    ],
                )
            )
            sm.risk_peak, sm.level = st.score, st.level
            if sm.detect_turn is None and st.score >= HIGH:
                sm.detect_turn = n
            if sm.critical_turn is None and st.level == "critical":
                sm.critical_turn = n
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
                "risk",
                {
                    "turn": n,
                    **explain(st, guess_language(turn.text)),
                    "stage": st.stage,
                    "active_tactics": active,
                },
            )

            if (
                self.alert_hook is not None
                and st.level in ("high", "critical")
                and st.level not in alerted
            ):
                alerted.add(st.level)
                await self.alert_hook(
                    st.level,
                    {
                        "session_id": sid,
                        "turn": n,
                        "score": st.score,
                        "tactics": active,
                        "scenario": scenario_id,
                    },
                )

            for rec in await store.ingest(turn.text, n, self.llm):
                await self.emit("evidence", rec.as_dict())

            if turn.done:
                sm.ended_reason = "scammer_disengaged"
                break

            if victim_provider is not None:
                reply_text = await victim_provider()
                if reply_text is None:
                    sm.ended_reason = "user_takeover"
                    break
                history.append(("victim", reply_text))
                sm.transcript.append({"turn": n, "speaker": "victim", "text": reply_text})
                await self.emit("transcript", {"turn": n, "speaker": "victim", "text": reply_text})
            elif mode == "honeypot":
                rep = await persona.reply(turn.text, history, store.types())
                history.append(("persona", rep.text))
                sm.persona_turns += 1
                sm.time_wasted_s += rep.seconds
                sm.guarded_outputs += int(rep.guarded)
                sm.transcript.append(
                    {
                        "turn": n,
                        "speaker": "persona",
                        "text": rep.text,
                        "move": rep.move_id,
                        "guarded": rep.guarded,
                    }
                )
                await self.emit(
                    "persona_reply",
                    {
                        "turn": n,
                        "text": rep.text,
                        "move": rep.move_id,
                        "time_wasted_s": sm.time_wasted_s,
                        "guarded": rep.guarded,
                    },
                )
            if pace_s:
                await asyncio.sleep(pace_s)
        else:
            sm.ended_reason = "max_turns"

        sm.evidence = [r.as_dict() for r in store.items()]
        await self._persist(sm, history, store, learn_turns)
        await self.emit(
            "summary",
            {
                "risk_peak": sm.risk_peak,
                "level": sm.level,
                "detect_turn": sm.detect_turn,
                "time_wasted_s": sm.time_wasted_s,
                "engaged_turns": sm.persona_turns,
                "identifier_types": sorted(store.types()),
                "memory_hit": sm.memory_hit,
                "ended_reason": sm.ended_reason,
                "incident_id": sm.incident_id,
                "session_id": sid,
            },
        )
        return sm

    async def _persist(
        self,
        sm: SessionSummary,
        history: list[tuple[str, str]],
        store: EvidenceStore,
        learn_turns: list[LearnTurn],
    ) -> None:
        if self.db is None or self.user_id is None:
            return
        sess = await self.db.get(Session, sm.session_id)
        if sess is None:
            return
        sess.risk_peak, sess.time_wasted_s = sm.risk_peak, sm.time_wasted_s
        sess.ended_at = datetime.now(UTC)
        if self.cipher is not None:
            for i, t in enumerate(sm.transcript):
                await repo.add_utterance(
                    self.db,
                    self.cipher,
                    session_id=sm.session_id,
                    turn=i,
                    speaker=t["speaker"],
                    text_plain=t["text"],
                )
        for r in store.items():
            self.db.add(
                EvidenceItem(
                    session_id=sm.session_id, type=r.type, value=r.value, confidence=r.confidence
                )
            )
        inc: Incident = await learn_session(
            self.db,
            session_id=sm.session_id,
            turns=learn_turns,
            detect_turn=sm.detect_turn,
            summary=f"{sm.scenario}: peak risk {sm.risk_peak}, {len(store.items())} identifiers",
            memory_hit_turn=(sm.memory_hit or {}).get("hit_turn"),
        )
        sm.incident_id = inc.id
        await self.db.commit()
