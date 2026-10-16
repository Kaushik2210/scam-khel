"""PII sanitizer: mask identifiers and pseudonymise family names before any LLM call."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_F = re.IGNORECASE | re.UNICODE

# Order matters: more specific / longer patterns first.
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("OTP", re.compile(r"(\b(?:otp|pin|cvv|code|ओटीपी)\b\D{0,15})\d{4,8}\b", _F)),
    ("CARD", re.compile(r"\b(?:\d{4}[\s-]?){3}\d{4}\b")),
    ("AADHAAR", re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")),
    ("PAN", re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")),
    ("IFSC", re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")),
    ("UPI", re.compile(r"\b[\w.\-]{2,}@[a-z][a-z0-9]{1,}\b(?!\.[a-z])", _F)),
    ("PHONE", re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")),
    ("ACCOUNT", re.compile(r"\b\d{9,18}\b")),
]


@dataclass
class Sanitized:
    text: str
    counts: dict[str, int] = field(default_factory=dict)
    pseudonyms: dict[str, str] = field(default_factory=dict)  # real name -> FAMILY_n

    @property
    def masked_any(self) -> bool:
        return bool(self.counts)


def sanitize(text: str, family_names: list[str] | None = None) -> Sanitized:
    counts: dict[str, int] = {}
    out = text
    for label, pat in _PATTERNS:
        if label == "OTP":
            out, n = pat.subn(lambda m: f"{m.group(1)}[OTP]", out)
        else:
            out, n = pat.subn(f"[{label}]", out)
        if n:
            counts[label] = counts.get(label, 0) + n
    pseudonyms: dict[str, str] = {}
    for i, name in enumerate(
        dict.fromkeys(n.strip() for n in (family_names or []) if n.strip()), 1
    ):
        pat = re.compile(rf"(?<!\w){re.escape(name)}(?!\w)", _F)
        out, n = pat.subn(f"FAMILY_{i}", out)
        if n:
            counts["FAMILY"] = counts.get("FAMILY", 0) + n
        pseudonyms[name] = f"FAMILY_{i}"
    return Sanitized(out, counts, pseudonyms)
