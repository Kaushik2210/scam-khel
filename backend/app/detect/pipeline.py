"""Run a full dialogue through tagger + risk engine (used by tests, evals and the orchestrator)."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.detect.risk import RiskEngine
from app.detect.tagger import Tagged, tag_utterance
from app.llm.client import LLMClient

SCORED_SPEAKERS = {"caller", "scammer"}


@dataclass
class TurnResult:
    index: int  # index in the original turn list
    tagged: Tagged
    score: int
    level: str


@dataclass
class DialogueResult:
    turns: list[TurnResult] = field(default_factory=list)
    peak: int = 0

    def first_turn_at(self, level_min: int) -> int | None:
        return next((t.index for t in self.turns if t.score >= level_min), None)

    def tactic_turns(self) -> list[list[str]]:
        return [[t.id for t in r.tagged.tactics if t.confidence >= 0.5] for r in self.turns]


async def analyze_dialogue(
    turns: list[dict[str, str]], llm: LLMClient | None = None
) -> DialogueResult:
    engine = RiskEngine()
    res = DialogueResult()
    for i, turn in enumerate(turns):
        if turn["s"] not in SCORED_SPEAKERS:
            continue
        tagged = await tag_utterance(turn["t"], llm)
        st = engine.update(tagged)
        res.turns.append(TurnResult(i, tagged, st.score, st.level))
        res.peak = max(res.peak, st.score)
    return res
