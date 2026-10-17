"""eval-lite (offline, runs in CI): guards against regressions in the headline metrics."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evals.run_eval import detection, honeypot_and_memory, load  # noqa: E402


async def test_detection_floor_and_no_false_positives():
    d = await detection(load(), None)
    o = d["overall"]
    assert o["scam"] >= 25 and o["legit"] >= 15
    assert o["recall"] >= 0.9 and o["precision"] >= 0.95
    assert o["fp_rate_legit"] == 0.0
    assert d["tuned_set"]["critical_by_payment_rate"] == 1.0


async def test_honeypot_safety_and_memory_benefit():
    h = await honeypot_and_memory(None)
    assert h["persona_leakage_rate"] == 0
    assert h["mean_identifier_types"] >= 5
    assert h["memory_mean_turns_saved"] > 0
    assert all(m["second_detect_turn"] <= m["first_detect_turn"] for m in h["memory"])
