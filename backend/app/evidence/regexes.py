"""Regex evidence extraction (identifiers a scammer discloses)."""

from __future__ import annotations

import re
from dataclasses import dataclass

_F = re.IGNORECASE | re.UNICODE


@dataclass(frozen=True)
class Candidate:
    type: str
    value: str
    span: str


def _norm_phone(s: str) -> str:
    d = re.sub(r"\D", "", s)
    return "+91" + d[-10:]


_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("phone", re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")),
    ("upi", re.compile(r"(?<![\w.\-])[\w.\-]{2,}@[a-z][a-z0-9]{1,}\b(?!\.[a-z])", _F)),
    ("ifsc", re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")),
    (
        "account",
        re.compile(
            r"\b(?:account|a/c|acct)(?:\s*(?:no\.?|number))?\s*[:#-]?\s*([A-Z]{0,4}\d{9,18})\b", _F
        ),
    ),
    ("apk", re.compile(r"[\w./:-]*\b[\w-]+\.apk\b", _F)),
    ("url", re.compile(r"https?://[^\s\"'<>)]+|\bwww\.[^\s\"'<>)]+", _F)),
    (
        "badge_id",
        re.compile(
            r"\b(?:badge|employee|officer|id)\s*(?:no\.?|number|id)?\s*[:#-]?\s*([A-Z]{2,5}-?\d{3,8})\b",
            _F,
        ),
    ),
    (
        "case_id",
        re.compile(
            r"\b(?:case|fir|reference|ref|warrant)\s*(?:no\.?|number|id)?\s*[:#-]?\s*([A-Z]{2,5}-?\d{3,8}|\d{4,8})\b",
            _F,
        ),
    ),
    (
        "officer_name",
        re.compile(
            r"\b(?i:inspector|officer|executive|sub-inspector|si|dcp|sir|mr\.?|mrs\.?)\s+"
            r"([A-Z][a-z]{2,15}(?:\s[A-Z][a-z]{2,15})?)\b"
        ),
    ),
    (
        "agency",
        re.compile(
            r"\b((?:[A-Z][A-Za-z]+\s){1,4}(?:Cell|Branch|Desk|Bureau|Department|Division|Directorate)"
            r"(?:\s\(SIMULATION\))?)"
        ),
    ),
    (
        "amount",
        re.compile(r"(?:₹|rs\.?|inr|rupees?)\s*([\d,]+(?:\.\d+)?(?:\s*(?:lakh|crore))?)", _F),
    ),
    (
        "deadline",
        re.compile(
            r"\b(within\s+\d+\s*(?:minutes?|mins?|hours?|hrs?)|by\s+(?:today|tonight)"
            r"|in\s+\d+\s*(?:minutes?|hours?))\b",
            _F,
        ),
    ),
]


def extract_candidates(text: str) -> list[Candidate]:
    out: list[Candidate] = []
    for typ, pat in _PATTERNS:
        for m in pat.finditer(text):
            raw = m.group(1) if pat.groups else m.group(0)
            val = raw.strip().rstrip(".,;")
            if typ == "phone":
                val = _norm_phone(val)
            elif typ == "upi":
                val = val.lower()
            elif typ == "ifsc":
                val = val.upper()
            elif typ == "amount":
                val = "Rs " + val.replace(" ", "")
            out.append(Candidate(typ, val, m.group(0).strip()))
    return out
