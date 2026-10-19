"""Deterministic multilingual (English / Hinglish / Devanagari Hindi) tactic rules."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.detect.taxonomy import TACTICS

_F = re.IGNORECASE | re.UNICODE


def _c(p: str) -> re.Pattern[str]:
    return re.compile(p, _F)


# tactic id -> [(pattern, confidence)]
RULES: dict[str, list[tuple[re.Pattern[str], float]]] = {
    "authority_impersonation": [
        (
            _c(
                r"\b(cbi|enforcement directorate|narcotics|ncb|cyber ?crime (cell|branch|police)"
                r"|crime branch|customs (officer|department)|trai\b|income tax (officer|department)"
                r"|supreme court|high court|(mumbai|delhi|cyber) police|police (officer|inspector"
                r"|department|station|headquarters)|inspector|dcp\b|national crime"
                r"|crime verification cell|investigation (bureau|agency)|ed officer)"
            ),
            0.9,
        ),
        (_c(r"पुलिस|सीबीआई|कस्टम|साइबर क्राइम|अदालत|इंस्पेक्टर|नारकोटिक्स|ट्राई\b"), 0.9),
        (_c(r"\b(police|pulis|thana)\b"), 0.8),
        (
            _c(
                r"\b(bijli (vibhag|board|office|karmi)|electricity (department|board|office|authority)"
                r"|power (corporation|department|board))\b"
            ),
            0.8,
        ),
        (_c(r"बिजली विभाग|विद्युत विभाग|पावर कॉर्पोरेशन"), 0.8),
        (
            _c(
                r"\b(bank (manager|officer|executive)|customer care|kyc (team|department)"
                r"|from (the )?bank)\b"
            ),
            0.55,
        ),
    ],
    "fear_arrest_threat": [
        (
            _c(
                r"\b(arrest(ed)?|warrant|jail|prison|custody|case (has been |is |was )?"
                r"(registered|filed)|legal action|prosecut\w*|criminal|money laundering"
                r"|narcotics|drugs?|illegal|fir\b|giraftar|girftaar|case darj)\b"
            ),
            0.9,
        ),
        (_c(r"गिरफ्तार|वारंट|जेल|केस दर्ज|अवैध|मनी लॉन्ड्रिंग|ड्रग|हिरासत"), 0.9),
        (
            _c(
                r"\b(connection|line|bijli|power|service|account)\b.{0,20}\b(kat|cut|disconnect\w*|band|freez\w*|suspend\w*)\b"
                r"|\b(kat|cut|disconnect\w*|band)\s+(jayega|karenge|kar denge|ho jayega)\b"
            ),
            0.7,
        ),
        (_c(r"कनेक्शन (कट|बंद)|बिजली कट|लाइन कट"), 0.7),
        (_c(r"\b(blocked|freez\w*|frozen|seiz\w*|disconnect(ed|ion)?|suspend\w*)\b"), 0.5),
    ],
    "isolation_secrecy": [
        (
            _c(
                r"\b(do not|don'?t|dont|never)\s+(tell|inform|discuss|speak|contact|talk)"
                r".{0,35}(anyone|anybody|family|relatives|friends|police|bank|lawyer|children"
                r"|son|daughter|neighbou?rs)"
            ),
            0.95,
        ),
        (
            _c(
                r"\b(do not|don'?t|dont|never)\s+share\s+(this|it|the case|about this"
                r"|these details|any of this)\b.{0,30}(anyone|anybody|family|others?)"
            ),
            0.95,
        ),
        (
            _c(
                r"\b(kisi ?ko|ghar (waalon|walon) ko|family ko)\b.{0,25}\b(mat|na|nahi|nahin)\b"
                r".{0,20}(bata|bol|batana|batao|batayen)"
            ),
            0.95,
        ),
        (_c(r"किसी को.{0,12}(मत|न|नहीं).{0,15}(बता|बोल)"), 0.95),
        (
            _c(
                r"\b(keep (this|it)?\s*(strictly )?confidential|maintain secrecy|strictly confidential)\b"
            ),
            0.85,
        ),
        (_c(r"गोपनीय रखें|गुप्त रखें"), 0.85),
        (_c(r"\b(confidential|top secret|secret case|secrecy)\b"), 0.6),
    ],
    "stay_on_camera_digital_arrest": [
        (_c(r"digital(ly)? arrest|डिजिटल अरेस्ट|house arrest"), 1.0),
        (
            _c(
                r"\b(stay|keep|remain)\b.{0,25}(on (the )?(video|camera|call|line)|camera on"
                r"|video call)"
            ),
            0.9,
        ),
        (
            _c(
                r"\b(do not|don'?t|dont|never)\s+(disconnect|cut|hang up|end|leave|switch off)"
                r".{0,20}(call|video|line|camera|phone)"
            ),
            0.9,
        ),
        (_c(r"\bcamera on\b|camera on rakh|call (mat|na) kat|video call par rah"), 0.9),
        (_c(r"कैमरा (चालू|ऑन)|वीडियो कॉल पर|कॉल (मत|न) काट"), 0.9),
    ],
    "urgency_deadline": [
        (
            _c(
                r"\b(immediately|right now|within \d+ ?(minutes?|mins?|hours?|hrs?)"
                r"|in \d+ ?(minutes?|mins?|hours?)|today itself|by (today|tonight|end of (the )?day)"
                r"|last (chance|warning)|without delay|urgent(ly)?|asap|expires? (today|tonight)"
                r"|before (midnight|5 ?pm))\b"
            ),
            0.7,
        ),
        (
            _c(
                r"\b(turant|abhi ke abhi|foran|jaldi|aaj hi|aaj raat|aaj shaam|by tonight"
                r"|ek ghante|\d+ ?(minute|ghante) mein)\b"
            ),
            0.7,
        ),
        (_c(r"तुरंत|अभी के अभी|जल्दी|आज ही|आज रात|आज शाम|घंटे में|मिनट में"), 0.7),
    ],
    "fake_case_or_badge_id": [
        (
            _c(
                r"\b(case|fir|badge|warrant|ref(erence)?)\s*(no\.?|number|id)?\s*[:#-]?\s*"
                r"[A-Z]{0,5}[-/]?\d{3,}[A-Z0-9/-]*"
            ),
            0.8,
        ),
        (_c(r"(केस|एफआईआर|बैज)\s*(नंबर|संख्या)?\s*[:#-]?\s*[A-Z0-9/-]{4,}"), 0.8),
    ],
    "document_demand": [
        (
            _c(
                r"\b(send|share|give|provide|tell|read out|submit|verify|confirm|bhej\w*|bata\w*)"
                r"\b.{0,30}(aadhaar|aadhar|pan (card|number)|\bpan\b|passport|bank (account|statement"
                r"|details)|account (number|details)|debit card|credit card|card (number|details)"
                r"|cvv|photo ?id|identity (proof|card))"
            ),
            0.8,
        ),
        (_c(r"(aadhaar|aadhar|pan card|account number).{0,25}(bhej|bata|do\b|dijiye|dena)"), 0.8),
        (_c(r"(आधार|पैन|खाता संख्या).{0,20}(भेज|बता|दीजिए|दें|दो)"), 0.8),
        (_c(r"\bbring\b.{0,30}(aadhaar|aadhar|pan|id proof|identity)"), 0.5),
    ],
    "safe_account_transfer": [
        (
            _c(
                r"(transfer|send|deposit|move|shift|pay)\b.{0,50}\b(safe|secure|secured|verification"
                r"|supervision|rbi|government|escrow|audit|temporary|holding|neutral)\s+"
                r"(bank\s+)?(account|a/c)"
            ),
            1.0,
        ),
        (_c(r"\b(safe|secure|verification|rbi) account (mein|me|par)\b"), 1.0),
        (_c(r"सुरक्षित (खाते|अकाउंट)|सेफ अकाउंट|वेरिफिकेशन अकाउंट"), 1.0),
    ],
    "verification_fee_or_deposit": [
        (
            _c(
                r"\b(pay|deposit|transfer|send|remit|submit)\b.{0,30}\b(fine|fee|fees|charges?"
                r"|penalty|bail|clearance|processing|settlement|bond|security deposit)\b"
            ),
            0.85,
        ),
        (_c(r"\b(jurmana|fees? bhar|paise jama|jama karwa|bail amount|rupay jama)\b"), 0.85),
        (_c(r"जुर्माना|शुल्क.{0,15}(जमा|भर)|जमानत राशि|पैसे जमा"), 0.85),
    ],
    "remote_access_app_request": [
        (
            _c(
                r"\b(install|download|open|start|use)\b.{0,25}(anydesk|teamviewer|quick ?support"
                r"|rustdesk|screen ?shar\w*|remote (access|support|desktop)|support app)"
            ),
            1.0,
        ),
        (_c(r"\bshare (your )?screen\b|एनीडेस्क|स्क्रीन शेयर"), 0.95),
    ],
    "otp_request": [
        (
            _c(
                r"\b(share|tell|send|give|read( out)?|provide|enter|forward|bata\w*|bhej\w*)\b"
                r".{0,25}(\botp\b|one[- ]time (password|code)|\bpin\b|\bcvv\b|verification code)"
            ),
            0.9,
        ),
        (_c(r"\botp\b.{0,15}(batao|bataiye|bhejiye|do\b|dijiye|share karo)"), 0.9),
        (_c(r"ओटीपी.{0,15}(बताएं|बताइए|भेजें|दें|बताओ)"), 0.9),
    ],
    "link_or_apk_push": [
        (
            _c(
                r"\b(click|open|tap|visit|go to|follow|download|install)\b.{0,25}"
                r"(link|url|https?://|www\.|\.apk|\bapk\b)"
            ),
            0.75,
        ),
        (_c(r"\.apk\b"), 0.8),
        (_c(r"https?://\S+|\bbit\.ly/\S+"), 0.45),
        (_c(r"लिंक (पर )?(क्लिक|खोल)"), 0.75),
    ],
    "family_member_implicated": [
        (
            _c(
                r"\b(your|aapka|aapke|aapki)\s+(son|daughter|husband|wife|mother|father|brother"
                r"|sister|grandson|granddaughter|nephew|beta|beti|bete|pati|patni)\b.{0,60}"
                r"(arrest\w*|custody|accident|detained|caught|involved|case|police|kidnap\w*"
                r"|giraftar|pakda|hospital)"
            ),
            0.9,
        ),
        (_c(r"आपका (बेटा|बेटी|पति|पत्नी|भाई|बहन).{0,50}(गिरफ्तार|पकड़|एक्सीडेंट|हिरासत)"), 0.9),
    ],
}

# Tactics where "never share / do not send ..." is a *warning*, not a demand.
NEGATION_SENSITIVE = {
    "otp_request",
    "document_demand",
    "link_or_apk_push",
    "remote_access_app_request",
    "safe_account_transfer",
    "verification_fee_or_deposit",
}
_PRE_NEG = re.compile(
    r"(?:never|do not|don'?t|dont|not|no one will|nobody will|kabhi nahi)\s+(?:\w+\s+){0,3}$", _F
)
_INNER_NEG = re.compile(r"\b(never|mat|nahi|nahin)\b|\bdo not\b|\bdon'?t\b|न बता|मत|नहीं", _F)

# Every repetition here is bounded. An open-ended `\d{3,}` followed by `.{0,30}` is polynomial on
# a long digit run: the match is retried from every digit and each try backtracks through the
# whole run, so a few thousand digits in one utterance would stall the event loop for seconds.
# No real amount has more than 15 digits, and a bounded run still matches inside a longer one.
_MONEY = _c(
    r"\b(transfer|send|pay|deposit|remit|bhej\w{0,20}|jama|submit)\b.{0,40}"
    r"(rs\.?|₹|rupees?|inr|lakh|crore|\d{3,15}|amount|money|funds?|paise)"
    r"|(भेज|जमा|ट्रांसफर).{0,30}(रुपये|राशि|पैसे|\d{3,15})"
    r"|(rs\.?|₹|rupees?|rupay\w{0,20}|lakh|crore|\d{3,15}|रुपये|राशि|पैसे).{0,30}"
    r"\b(bhej\w{0,20}|transfer|jama|deposit|send|pay)\b"
    r"|(रुपये|राशि|पैसे|\d{3,15}).{0,30}(भेज|जमा|ट्रांसफर)"
)


@dataclass(frozen=True)
class TacticHit:
    id: str
    confidence: float
    span: str


def _negated(tactic: str, text: str, m: re.Match[str]) -> bool:
    if tactic not in NEGATION_SENSITIVE:
        return False
    if _PRE_NEG.search(text[max(0, m.start() - 24) : m.start()]):
        return True
    return bool(_INNER_NEG.search(m.group(0)))


def detect_rules(text: str) -> list[TacticHit]:
    """Best (highest-confidence, non-negated) hit per tactic."""
    out: dict[str, TacticHit] = {}
    for tid, pats in RULES.items():
        assert tid in TACTICS
        for pat, conf in pats:
            for m in pat.finditer(text):
                if _negated(tid, text, m):
                    continue
                if tid not in out or conf > out[tid].confidence:
                    out[tid] = TacticHit(tid, conf, m.group(0).strip()[:120])
    return list(out.values())


def has_money_request(text: str) -> bool:
    for m in _MONEY.finditer(text):
        if not _PRE_NEG.search(text[max(0, m.start() - 24) : m.start()]):
            return True
    return False


# Public-awareness / advisory text ("beware of digital arrest scams ...") quotes scam vocabulary
# to warn about it. Cues are deliberately specific.
_AWARENESS = re.compile(
    r"\b(beware of|public advisory|awareness|be aware|stay alert|do not fall for|don'?t fall for"
    r"|scam alert|fraud alert|if you receive such a call|never (?:arrest|ask|asks|demand))\b"
    r"|\b(?:dial|call) 1930\b|cybercrime\.gov\.in|सावधान|जागरूक",
    re.IGNORECASE | re.UNICODE,
)
DEMAND_TACTICS = NEGATION_SENSITIVE  # un-negated demands (otp, documents, links, money...)


def is_awareness(text: str) -> bool:
    return bool(_AWARENESS.search(text))
