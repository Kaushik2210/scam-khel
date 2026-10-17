"""Output guard: nothing the persona says may leak real-looking data or comply with the scam."""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field

from app.persona.decoys import ALLOWED_IFSC, ALLOWED_UPI
from app.persona.stalling import safe_stall_line

_F = re.IGNORECASE | re.UNICODE

_DIGIT_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("card", re.compile(r"(?<!\d)(?:\d[\s-]?){13,16}(?!\d)")),
    ("aadhaar", re.compile(r"(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)")),
    ("pan", re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")),
    ("phone", re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")),
    ("otp", re.compile(r"\b(?:otp|pin|cvv|code|password|ओटीपी)\b\D{0,20}\d{4,8}(?!\d)", _F)),
    (
        "otp",
        re.compile(r"(?<!\d)\d{4,8}\s*(?:is|hai|h)\s*(?:my|mera|meri)?\s*(?:otp|pin|code)", _F),
    ),
    ("account", re.compile(r"(?<!\d)\d{9,18}(?!\d)")),
    ("url", re.compile(r"https?://|www\.|\.apk\b", _F)),
]
_UPI = re.compile(r"[\w.\-]{2,}@[a-z][a-z0-9]{1,}\b(?!\.[a-z])", _F)
_IFSC = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")

_COMPLY = [
    r"\bi\s*(?:will|'ll|shall|am going to|have|had|just)\s+(?:now\s+|already\s+)?"
    r"(?:transfer(?:red)?|sent|send|paid|pay|install(?:ed)?|click(?:ed)?|download(?:ed)?"
    r"|shar(?:e|ed)|giv(?:e|en))\b",
    r"\bhere\s+(?:is|are)\s+my\s+(?:otp|aadhaar|aadhar|pin|account|card|password)",
    r"\bmain\s+(?:abhi\s+)?(?:bhej|transfer|install|click|pay|de)\w*\s+(?:raha|rahi|deti|dungi|dunga|"
    r"karti|karta|diya|di)\b",
    r"\b(?:bhej|transfer|jama|install|download)\s+(?:kar\s+)?(?:diya|di|liya|kar diya)\b",
    r"\blink\s+khol\s+(?:liya|diya|rahi|raha)\b",
    r"\bok(?:ay)?[,.\s]+(?:i(?:'ll| will)|sending|paying|transferring)\b",
    r"\bsending\s+(?:the\s+)?(?:money|amount|payment)\b",
    r"\b(?:paise|rupay|amount)\s+(?:bhej|transfer)\s+(?:rahi|raha|deti|dungi|dunga)\b",
]
_REVEAL = [
    r"\b(?:ai|a\.i\.|artificial intelligence|language model|chatbot|bot|honeypot|llm"
    r"|nemotron|simulation|scam detect\w*|i am programmed|as an ai)\b",
]
_COMPLY_RE = [re.compile(p, _F) for p in _COMPLY]
_REVEAL_RE = [re.compile(p, _F) for p in _REVEAL]
MAX_CHARS = 420


@dataclass
class GuardResult:
    ok: bool
    text: str  # always safe to emit
    violations: list[str] = field(default_factory=list)


def find_violations(text: str) -> list[str]:
    v: list[str] = []
    for name, pat in _DIGIT_RULES:
        if pat.search(text):
            v.append(name)
    for m in _UPI.finditer(text):
        if m.group(0).lower() not in ALLOWED_UPI:
            v.append("upi")
    for m in _IFSC.finditer(text):
        if m.group(0).upper() not in ALLOWED_IFSC:
            v.append("ifsc")
    if any(p.search(text) for p in _COMPLY_RE):
        v.append("compliance")
    if any(p.search(text) for p in _REVEAL_RE):
        v.append("reveal")
    if len(text) > MAX_CHARS:
        v.append("too_long")
    return list(dict.fromkeys(v))


def guard(text: str, rng: random.Random | None = None) -> GuardResult:
    """Block and rewrite. A violating reply is replaced wholesale by a clean stalling line."""
    rng = rng or random.Random()  # noqa: S311
    text = text.strip()
    violations = find_violations(text)
    if not text:
        violations.append("empty")
    if not violations:
        return GuardResult(True, text)
    safe = safe_stall_line(rng)
    assert not find_violations(safe)
    return GuardResult(False, safe, violations)
