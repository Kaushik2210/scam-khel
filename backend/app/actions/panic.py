"""'I already sent money' panic flow: checklist, prefilled form, 1930 call script, complaint."""

from __future__ import annotations

from datetime import date, time
from typing import Literal

from pydantic import BaseModel, Field

from app.actions.complaint import ComplaintData, build_markdown

CHECKLIST = {
    "en": [
        "Call 1930 (National Cyber Crime Helpline) right now. Faster is better.",
        "Call your bank's fraud line and ask them to hold/trace the transfer.",
        "Write down the transaction details (the form below helps).",
        "Take screenshots: call log, chat, payment receipt, the beneficiary details.",
        "Do not send any more money, even to 'get the money back'.",
        "File the complaint at cybercrime.gov.in (a draft is prepared for you).",
        "Tell a family member. You are not at fault: this is organised fraud.",
    ],
    "hi": [
        "अभी 1930 (राष्ट्रीय साइबर क्राइम हेल्पलाइन) पर कॉल करें। जितनी जल्दी, उतना बेहतर।",
        "अपने बैंक की फ्रॉड लाइन पर कॉल करके ट्रांसफर रोकने/ट्रेस करने को कहें।",
        "लेन-देन का विवरण लिख लें (नीचे का फॉर्म मदद करेगा)।",
        "स्क्रीनशॉट लें: कॉल लॉग, चैट, भुगतान की रसीद, प्राप्तकर्ता का विवरण।",
        "और पैसे न भेजें, 'पैसे वापस पाने' के नाम पर भी नहीं।",
        "cybercrime.gov.in पर शिकायत दर्ज करें (ड्राफ्ट तैयार है)।",
        "परिवार के किसी सदस्य को बताएं। आपकी गलती नहीं है: यह संगठित धोखाधड़ी है।",
    ],
}


class TransactionDetails(BaseModel):
    amount_inr: float = Field(gt=0, le=1e10)
    txn_date: date | None = None
    txn_time: time | None = None
    mode: Literal["upi", "neft_imps_rtgs", "card", "cash", "other"] = "upi"
    beneficiary_name: str = Field("", max_length=120)
    beneficiary_account_or_upi: str = Field("", max_length=64)
    bank_name: str = Field("", max_length=80)
    txn_reference: str = Field("", max_length=64)
    caller_phone: str = Field("", max_length=20)

    def as_rows(self) -> dict[str, str]:
        rows = {
            "Amount": f"Rs {self.amount_inr:,.2f}",
            "Date": self.txn_date.isoformat() if self.txn_date else "",
            "Time": self.txn_time.strftime("%H:%M") if self.txn_time else "",
            "Mode": self.mode,
            "Beneficiary name": self.beneficiary_name,
            "Beneficiary account / UPI": self.beneficiary_account_or_upi,
            "Beneficiary bank": self.bank_name,
            "Transaction reference": self.txn_reference,
            "Caller phone": self.caller_phone,
        }
        return {k: (v or "(fill in)") for k, v in rows.items()}


def call_script_1930(tx: TransactionDetails, lang: str = "en") -> str:
    r = tx.as_rows()
    if lang == "hi":
        return (
            "नमस्ते, मैं साइबर ठगी की शिकायत करना चाहता/चाहती हूँ। मुझसे वीडियो कॉल पर "
            f"गिरफ्तारी का डर दिखाकर {r['Amount']} ट्रांसफर करवाए गए। तारीख/समय: {r['Date']} "
            f"{r['Time']}। प्राप्तकर्ता: {r['Beneficiary name']}, खाता/UPI: "
            f"{r['Beneficiary account / UPI']}, बैंक: {r['Beneficiary bank']}। "
            f"संदर्भ संख्या: {r['Transaction reference']}। ठग का फोन: {r['Caller phone']}। "
            "कृपया तुरंत खाता फ्रीज़ कराएं और शिकायत संख्या दें।"
        )
    return (
        "Hello, I want to report a cyber fraud. I was threatened with arrest on a video call "
        f"and made to transfer {r['Amount']}. Date/time: {r['Date']} {r['Time']}. "
        f"Beneficiary: {r['Beneficiary name']}, account/UPI: {r['Beneficiary account / UPI']}, "
        f"bank: {r['Beneficiary bank']}. Transaction reference: {r['Transaction reference']}. "
        f"Caller's phone: {r['Caller phone']}. Please freeze the beneficiary account immediately "
        "and give me a complaint number."
    )


def panic_bundle(
    tx: TransactionDetails,
    lang: str = "en",
    incident: ComplaintData | None = None,
) -> dict[str, object]:
    d = incident or ComplaintData(
        incident_id=None,
        scenario="reported by user",
        simulation=False,
        risk_peak=0,
        summary="Complainant reports being coerced into transferring money by a caller "
        "threatening arrest over video call.",
    )
    d.transaction = tx.as_rows()
    code = "hi" if lang == "hi" else "en"
    return {
        "helpline": "1930",
        "portal": "https://cybercrime.gov.in",
        "checklist": CHECKLIST[code],
        "transaction_form": tx.as_rows(),
        "call_script": call_script_1930(tx, code),
        "complaint_markdown": build_markdown(d),
        "note": "Draft only. SCAM-KHEL never files anything for you.",
    }
