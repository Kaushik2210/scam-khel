"""Case, FIR, badge and account number patterns must stay linear on hostile whitespace.

The old patterns chained three unbounded whitespace runs with optional words and
punctuation between them, so after a keyword followed by n spaces the engine tried O(n^3)
ways to split the run: about 5 s for "case" + 1,000 spaces and over 25 s for 2,000. A single
2,000-character websocket message could freeze the API.
"""

import time

import pytest

from app.detect.rules import detect_rules
from app.evidence.regexes import extract_candidates

# The old patterns needed minutes at these sizes; the fixed ones need milliseconds.
BUDGET_S = 2.0
SPACES = 20_000

HOSTILE = [
    "case" + " " * SPACES,
    "case no" + " " * SPACES,
    "case number" + " " * SPACES + "!",
    "fir" + " " * SPACES,
    "badge" + " " * SPACES,
    "warrant" + " " * SPACES,
    "reference id" + " " * SPACES,
    "account" + " " * SPACES,
    "account no" + " " * SPACES + "x",
    "officer" + " " * SPACES,
    "केस" + " " * SPACES,
    "केस नंबर" + " " * SPACES + "!",
    "एफआईआर" + " " * SPACES,
    "बैज" + " " * SPACES,
    "case" + " \t" * (SPACES // 2),
    "case " * (SPACES // 5),
]


def elapsed(fn) -> float:
    start = time.perf_counter()
    fn()
    return time.perf_counter() - start


@pytest.mark.parametrize("text", HOSTILE, ids=lambda t: f"{t[:12].strip()!r}x{len(t)}")
def test_detection_and_evidence_are_fast_on_hostile_whitespace(text):
    assert elapsed(lambda: detect_rules(text)) < BUDGET_S
    assert elapsed(lambda: extract_candidates(text)) < BUDGET_S


@pytest.mark.parametrize(
    "text,span",
    [
        ("Your case number 4567890 is registered", "case number 4567890"),
        ("officer badge no MH12345 calling", "badge no MH12345"),
        ("this FIR : CBI-2024 is open", "FIR : CBI-2024"),
        ("warrant ref   id # 998877 issued", "ref   id # 998877"),
        ("case" + " " * 10 + "MH1234", "case" + " " * 10 + "MH1234"),  # the most spaces allowed
        ("Case#555555 pending", "Case#555555"),
    ],
)
def test_case_and_badge_numbers_are_still_detected(text, span):
    hits = [h for h in detect_rules(text) if h.id == "fake_case_or_badge_id"]
    assert [h.span for h in hits] == [span]


@pytest.mark.parametrize(
    "text",
    ["केस नंबर: MH1234567", "केस MH1234567", "एफआईआर संख्या  ABC12345", "बैज #XX7777"],
)
def test_hindi_case_numbers_are_still_detected(text):
    assert [h.id for h in detect_rules(text) if h.id == "fake_case_or_badge_id"] == [
        "fake_case_or_badge_id"
    ]


@pytest.mark.parametrize(
    "text,kind,value",
    [
        ("Your case number 4567890 is registered", "case_id", "4567890"),
        ("FIR no. CBI-2024 filed", "case_id", "CBI-2024"),
        ("officer badge no MH12345 calling", "badge_id", "MH12345"),
        ("employee id: AB-1234", "badge_id", "AB-1234"),
        ("send to account no 123456789012 now", "account", "123456789012"),
        ("a/c # 987654321098", "account", "987654321098"),
    ],
)
def test_evidence_extraction_is_unchanged(text, kind, value):
    found = {(c.type, c.value) for c in extract_candidates(text)}
    assert (kind, value) in found


@pytest.mark.parametrize(
    "text", ["the weather is nice", "my id is 12", "case closed", "badge", "account", ""]
)
def test_unrelated_text_is_not_flagged(text):
    assert [h for h in detect_rules(text) if h.id == "fake_case_or_badge_id"] == []
    assert [
        c for c in extract_candidates(text) if c.type in {"case_id", "badge_id", "account"}
    ] == []
