"""Risk engine: 0-100 score from tactic severity, co-occurrence, stage progression, money."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.detect.tagger import STAGES, Tagged, TaggedTactic
from app.detect.taxonomy import TACTICS

CAUTION, HIGH, CRITICAL = 40, 70, 85
MIN_CONF = 0.5  # below this a tactic is recorded but does not score
STRONG_CONF = 0.7

LE_AUTHORITY_CONF = 0.8  # law-enforcement impersonation (bank-ish mentions score lower)
COERCIVE = {
    "fear_arrest_threat",
    "isolation_secrecy",
    "stay_on_camera_digital_arrest",
    "family_member_implicated",
}
# (needs-all-of A, needs-any-of B, bonus)
COMBOS: list[tuple[str, set[str], int]] = [
    ("authority_impersonation", {"fear_arrest_threat", "family_member_implicated"}, 12),
    (
        "isolation_secrecy",
        {"authority_impersonation", "fear_arrest_threat", "stay_on_camera_digital_arrest"},
        10,
    ),
    ("stay_on_camera_digital_arrest", {"fear_arrest_threat", "authority_impersonation"}, 10),
    ("document_demand", {"authority_impersonation", "fear_arrest_threat"}, 10),
    ("otp_request", {"authority_impersonation", "fear_arrest_threat", "urgency_deadline"}, 12),
    (
        "remote_access_app_request",
        {"authority_impersonation", "fear_arrest_threat", "urgency_deadline"},
        12,
    ),
]


def level_for(score: int) -> str:
    if score >= CRITICAL:
        return "critical"
    if score >= HIGH:
        return "high"
    if score >= CAUTION:
        return "caution"
    return "low"


@dataclass
class RiskState:
    score: int = 0
    level: str = "low"
    stage: str = "contact"
    tactics: dict[str, float] = field(default_factory=dict)  # id -> best confidence so far
    payment_demand_seen: bool = False
    turns: int = 0
    reasons: list[str] = field(default_factory=list)


class RiskEngine:
    """Feed it each scammer-side turn; the score never falls during a conversation."""

    def __init__(self) -> None:
        self.state = RiskState()

    def update(self, tagged: Tagged) -> RiskState:
        s = self.state
        s.turns += 1
        for t in tagged.tactics:
            if t.confidence > s.tactics.get(t.id, 0.0):
                s.tactics[t.id] = t.confidence
        strong = {k for k, c in s.tactics.items() if c >= MIN_CONF}
        reasons: list[str] = []

        base = sum(TACTICS[k].severity * 3 * s.tactics[k] for k in strong)
        bonus = 0
        for a, anyof, pts in COMBOS:
            if a in strong and strong & anyof:
                bonus += pts
                reasons.append(f"{a}+{'/'.join(sorted(strong & anyof))}")

        stage_idx = max(STAGES.index(tagged.stage), STAGES.index(s.stage))  # stages only advance
        s.stage = STAGES[stage_idx]
        bonus += 3 * stage_idx

        payment_now = tagged.money_request or any(
            t.id in {"safe_account_transfer", "verification_fee_or_deposit"} and t.confidence >= 0.8
            for t in tagged.tactics
        )
        s.payment_demand_seen = s.payment_demand_seen or payment_now

        score = base + bonus
        if payment_now:
            score += 15  # an explicit money ask is the decisive signal
        # Payment demand under coercion is critical by definition.
        coercive = {k for k in COERCIVE if s.tactics.get(k, 0) >= STRONG_CONF}
        le_urgent = (
            s.tactics.get("authority_impersonation", 0) >= LE_AUTHORITY_CONF
            and s.tactics.get("urgency_deadline", 0) >= STRONG_CONF
        )
        if s.payment_demand_seen and (coercive or le_urgent) and len(strong) >= 2:
            score = max(score, CRITICAL)
            reasons.append("payment demand under coercion")

        s.score = max(s.score, min(100, round(score)))  # monotonic within a conversation
        s.level = level_for(s.score)
        s.reasons = reasons
        return s


def active_tactics(state: RiskState) -> list[TaggedTactic]:
    return [TaggedTactic(id=k, confidence=c) for k, c in state.tactics.items() if c >= MIN_CONF]


# --- plain-language output --------------------------------------------------------------------

_EXPLAIN = {
    "en": {
        "low": "Nothing alarming so far, but stay alert.",
        "caution": "Some warning signs. Do not share personal details or money yet.",
        "high": "This looks like a scam. Do not pay, do not share codes, hang up.",
        "critical": "This is almost certainly a scam. Hang up now. Do not send any money.",
    },
    "hi": {
        "low": "अभी तक कुछ खतरनाक नहीं लगा, फिर भी सावधान रहें।",
        "caution": "कुछ खतरे के संकेत हैं। अभी कोई जानकारी या पैसे न दें।",
        "high": "यह धोखाधड़ी लग रही है। पैसे न दें, कोड न बताएं, फोन काट दें।",
        "critical": "यह लगभग निश्चित धोखाधड़ी है। अभी फोन काटें। कोई पैसा न भेजें।",
    },
}
_WHAT_TO_DO = {
    "en": [
        "Hang up. Police, CBI, ED and courts do not arrest people over video calls.",
        "Do not send money, share OTP/PIN, or install any app.",
        "If money was already sent, call 1930 immediately.",
        "Report at cybercrime.gov.in.",
        "Tell a family member now.",
    ],
    "hi": [
        "फोन काट दें। पुलिस, सीबीआई, ईडी या अदालत वीडियो कॉल पर गिरफ्तारी नहीं करती।",
        "पैसे न भेजें, OTP/PIN न बताएं, कोई ऐप इंस्टॉल न करें।",
        "अगर पैसे भेज दिए हैं तो तुरंत 1930 पर कॉल करें।",
        "cybercrime.gov.in पर शिकायत दर्ज करें।",
        "अभी परिवार के किसी सदस्य को बताएं।",
    ],
}


def explain(state: RiskState, lang: str = "en") -> dict[str, object]:
    code = "hi" if lang in ("hi", "hinglish") else "en"
    return {
        "level": state.level,
        "score": state.score,
        "summary": _EXPLAIN[code][state.level],
        "tactics": sorted(k for k, c in state.tactics.items() if c >= MIN_CONF),
        "what_to_do": _WHAT_TO_DO[code] if state.level in ("high", "critical") else [],
    }
