"""Complaint draft (Markdown). A DRAFT for the user to review; the app never files anything."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.detect.sanitizer import sanitize

DRAFT_BANNER = (
    "DRAFT - review and file at https://cybercrime.gov.in. "
    "If money was transferred, call helpline 1930 immediately."
)
DISCLAIMER = (
    "This is a machine-assisted draft, not legal advice. Check every statement before filing. "
    "SCAM-KHEL never submits anything on your behalf."
)


@dataclass
class ComplaintData:
    incident_id: int | None
    scenario: str
    simulation: bool
    risk_peak: int
    summary: str
    timeline: list[dict[str, Any]] = field(default_factory=list)  # turn, stage, tactics, risk
    evidence: list[dict[str, Any]] = field(default_factory=list)
    transcript: list[dict[str, Any]] = field(default_factory=list)  # turn, speaker, text
    verifications: list[dict[str, Any]] = field(default_factory=list)
    transaction: dict[str, str] | None = None  # from the panic flow
    final_analysis: dict[str, Any] | None = None  # DEEP-tier analysis, when an LLM was available
    generated: str = field(default_factory=lambda: datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"))


ANNEXURES = [
    "Screenshots of the call log / chat showing the caller's number",
    "Transaction receipt(s) / bank statement (if any money was sent)",
    "This transcript excerpt and identifier table",
    "Any messages, links or files received",
]
REQUESTED_ACTIONS = [
    "Register the complaint and investigate the offender(s) identified below",
    "Request the bank(s) to freeze/trace the beneficiary account(s) listed",
    "Request telecom operator action against the phone number(s) listed",
    "Provide acknowledgement / complaint number to the complainant",
]


def _redact(text: str, redact: bool) -> str:
    return sanitize(text).text if redact else text


def build_markdown(d: ComplaintData, redact: bool = True, max_excerpts: int = 12) -> str:
    L: list[str] = []
    if d.simulation:
        L += ["> **SIMULATION - generated from a fictional training scenario. Do not file.**", ""]
    L += ["# Cyber crime complaint - DRAFT", "", f"**{DRAFT_BANNER}**", "", f"_{DISCLAIMER}_", ""]
    L += [
        "## 1. Complainant (fill in)",
        "",
        "| Field | Value |",
        "|---|---|",
        "| Full name | ______________________ |",
        "| Age / gender | ______________________ |",
        "| Address | ______________________ |",
        "| Phone | ______________________ |",
        "| Email | ______________________ |",
        "",
    ]
    L += [
        "## 2. Summary of incident",
        "",
        d.summary or "(add a short summary)",
        "",
        f"- Generated: {d.generated}",
        f"- Peak risk score: {d.risk_peak}/100",
        f"- Pattern: {d.scenario}",
        "",
    ]
    if d.transaction:
        L += ["## 3. Transaction details (from panic flow)", "", "| Field | Value |", "|---|---|"]
        L += [f"| {k} | {v} |" for k, v in d.transaction.items()]
        L += [""]
    if d.final_analysis:
        L += [
            "## 3b. Analysis summary (AI-assisted, review before filing)",
            "",
            str(d.final_analysis.get("summary", "")),
            "",
        ]
        L += [f"- {m}" for m in d.final_analysis.get("modus_operandi", [])] + [""]
    L += [
        "## 4. Modus operandi timeline",
        "",
        "| Turn | Stage | Tactics | Risk |",
        "|---|---|---|---|",
    ]
    for t in d.timeline:
        L.append(
            f"| {t['turn']} | {t.get('stage', '')} | {', '.join(t.get('tactics', []))} "
            f"| {t.get('risk', '')} |"
        )
    L += [
        "",
        "## 5. Identifiers of the offender(s)",
        "",
        "| Type | Value | Confidence | Mentions |",
        "|---|---|---|---|",
    ]
    for e in d.evidence:
        L.append(
            f"| {e['type']} | `{e['value']}` | {e.get('confidence', '')} | {e.get('mentions', 1)} |"
        )
    if not d.evidence:
        L.append("| - | none extracted | - | - |")
    L += ["", f"## 6. Transcript excerpts{' (personal data redacted)' if redact else ''}", ""]
    for t in d.transcript[:max_excerpts]:
        who = "Caller" if t["speaker"] == "scammer" else "Complainant"
        L.append(f"- **{who} (turn {t['turn']}):** {_redact(t['text'], redact)}")
    if len(d.transcript) > max_excerpts:
        L.append(f"- ... {len(d.transcript) - max_excerpts} more turn(s) omitted")
    if d.verifications:
        L += ["", "## 7. Public-source checks (Tavily)", ""]
        for v in d.verifications:
            L.append(
                f"- **{v['kind']}** `{v['query']}` - {v['status']}"
                + (f" - {v['note']}" if v.get("note") else "")
            )
            L += [f"  - {s['title']} - {s['url']}" for s in v.get("sources", [])[:3]]
    L += ["", "## 8. Requested actions", ""] + [
        f"{i}. {a}" for i, a in enumerate(REQUESTED_ACTIONS, 1)
    ]
    L += ["", "## 9. Annexures to attach", ""] + [f"- [ ] {a}" for a in ANNEXURES]
    L += ["", "---", f"**{DRAFT_BANNER}**", ""]
    return "\n".join(L)
