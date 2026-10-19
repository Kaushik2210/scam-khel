from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel

SCENARIO_DIR = Path(__file__).parent / "scenarios"


class Stage(BaseModel):
    id: str
    goal: str
    min_turns: int = 1
    lines: list[str]


class Scenario(BaseModel):
    id: str
    title: str
    language: str
    agency: str
    identifiers: dict[str, str]
    patience: int = 5
    stages: list[Stage]

    def render(self, line: str) -> str:
        return line.format(agency=self.agency, **self.identifiers)


def _scenario_files() -> dict[str, Path]:
    return {p.stem: p for p in SCENARIO_DIR.glob("*.yaml") if p.is_file()}


@lru_cache
def load_scenario(scenario_id: str) -> Scenario:
    # The id only selects among files that exist in SCENARIO_DIR. The path that is opened comes
    # from that listing, never from the caller's string, so no input can name another file.
    path = _scenario_files().get(scenario_id)
    if path is None:
        raise KeyError(f"unknown scenario: {scenario_id!r}")
    sc = Scenario.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    if "(SIMULATION)" not in sc.agency:
        raise ValueError(f"{scenario_id}: agency must be labelled (SIMULATION)")
    return sc


def list_scenarios() -> list[Scenario]:
    return [load_scenario(p.stem) for p in sorted(SCENARIO_DIR.glob("*.yaml"))]
