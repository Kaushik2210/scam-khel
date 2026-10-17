"""Field-by-field helper for filing at cybercrime.gov.in.

The portal has no public filing API and needs the complainant's own login, OTP and captcha, so
SCAM-KHEL never submits anything. This module only prepares the text the user copies into the form.
"""

from __future__ import annotations

from typing import Any

from app.actions.complaint import ANNEXURES, ComplaintData
from app.detect.sanitizer import sanitize
from app.detect.taxonomy import TACTICS

PORTAL_URL = "https://cybercrime.gov.in"
HELPLINE = "1930"

_ID_LABELS = {
    "phone": "Suspect phone number",
    "upi": "Suspect UPI ID",
    "account": "Suspect bank account",
    "ifsc": "Suspect IFSC",
    "url": "Suspect website / link",
    "apk": "Suspect app / APK",
    "officer_name": "Name used by the caller",
    "badge_id": "Badge / employee ID quoted",
    "case_id": "Case / FIR number quoted",
    "agency": "Agency the caller claimed",
    "amount": "Amount demanded",
    "deadline": "Deadline imposed",
}


def build_narrative(d: ComplaintData, redact: bool = True) -> str:
    """Plain-language incident narrative, in the first person, from observed data only."""
    if d.final_analysis and d.final_analysis.get("narrative"):
        prefix = "[SIMULATION: fictional training scenario. Do not file.] " if d.simulation else ""
        return prefix + str(d.final_analysis["narrative"])
    tactics: list[str] = []
    for p in d.timeline:
        for t in p.get("tactics", []):
            if t in TACTICS and TACTICS[t].description not in tactics:
                tactics.append(TACTICS[t].description)
    agency = next(
        (e["value"] for e in d.evidence if e["type"] == "agency"), "a government or bank official"
    )
    parts = [
        f"I received a call/messages from a person claiming to be {agency}.",
    ]
    if tactics:
        parts.append(
            "During the conversation the caller: " + "; ".join(t.lower() for t in tactics[:8]) + "."
        )
    first = next((t for t in d.transcript if t["speaker"] == "scammer"), None)
    if first:
        txt = sanitize(first["text"]).text if redact else first["text"]
        parts.append(f'The first message was: "{txt[:300]}"')
    amount = next((e["value"] for e in d.evidence if e["type"] == "amount"), None)
    if amount:
        parts.append(f"The caller demanded {amount}.")
    if d.transaction:
        parts.append(
            f"I transferred {d.transaction.get('Amount', '(amount)')} on "
            f"{d.transaction.get('Date', '(date)')} to {d.transaction.get('Beneficiary account / UPI', '(account)')}."
        )
    else:
        parts.append("I have not transferred any money.")
    parts.append(
        "I request registration of this complaint and action against the identifiers listed."
    )
    if d.simulation:
        parts.insert(0, "[SIMULATION: generated from a fictional training scenario. Do not file.]")
    return " ".join(parts)


def build_report_fields(d: ComplaintData, redact: bool = True) -> dict[str, Any]:
    groups: list[dict[str, Any]] = []
    groups.append(
        {
            "group": "Complaint type",
            "fields": [
                {
                    "label": "Suggested category",
                    "value": "Online Financial Fraud / impersonation of officials (digital arrest)",
                },
                {"label": "Helpline if money was lost", "value": f"{HELPLINE} (call immediately)"},
            ],
        }
    )
    groups.append(
        {
            "group": "Incident description",
            "fields": [
                {
                    "label": "Narrative (paste into 'Additional information')",
                    "value": build_narrative(d, redact),
                }
            ],
        }
    )
    ids = [
        {"label": _ID_LABELS.get(e["type"], e["type"]), "value": str(e["value"])}
        for e in d.evidence
        if e["type"] in _ID_LABELS
    ]
    groups.append(
        {"group": "Suspect details", "fields": ids or [{"label": "None extracted", "value": "-"}]}
    )
    if d.transaction:
        groups.append(
            {
                "group": "Transaction details",
                "fields": [{"label": k, "value": v} for k, v in d.transaction.items()],
            }
        )
    groups.append(
        {
            "group": "Evidence to upload",
            "fields": [{"label": f"Item {i}", "value": a} for i, a in enumerate(ANNEXURES, 1)],
        }
    )
    return {
        "portal": PORTAL_URL,
        "helpline": HELPLINE,
        "simulation": d.simulation,
        "never_submits": True,
        "note": "You must log in, solve the captcha and press Submit yourself. SCAM-KHEL does not file anything.",
        "groups": groups,
    }
