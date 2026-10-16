"""Seed library of generic scam script patterns (authored; no real identifiers)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.models import ScamScript
from app.memory.retrieval import fts_upsert

AUTH = "authority_impersonation"
FEAR = "fear_arrest_threat"
ISO = "isolation_secrecy"
CAM = "stay_on_camera_digital_arrest"
URG = "urgency_deadline"
CASE = "fake_case_or_badge_id"
DOC = "document_demand"
SAFE = "safe_account_transfer"
FEE = "verification_fee_or_deposit"
APP = "remote_access_app_request"
OTP = "otp_request"
LINK = "link_or_apk_push"
FAM = "family_member_implicated"

# name -> (tactic order of first appearance, normalised phrase templates)
SEED_SCRIPTS: dict[str, tuple[list[str], list[str]]] = {
    "digital-arrest-parcel": (
        [AUTH, CASE, FEAR, ISO, CAM, DOC, SAFE],
        [
            "parcel in your name contains illegal items",
            "you are under digital arrest",
            "do not disconnect the video call",
            "do not tell anyone",
            "transfer to rbi safe account",
        ],
    ),
    "digital-arrest-money-laundering": (
        [AUTH, FEAR, CASE, DOC, ISO, CAM, SAFE],
        [
            "your aadhaar is linked to money laundering",
            "account used for hate transactions",
            "keep your camera on",
            "verification account for audit",
            "money will be refunded",
        ],
    ),
    "fake-customs-parcel": (
        [AUTH, FEAR, FEE, URG, SAFE],
        [
            "customs has seized your parcel",
            "pay clearance fee today",
            "foreign currency in package",
        ],
    ),
    "fake-police-family-accident": (
        [FAM, AUTH, URG, ISO, FEE],
        ["your son has been arrested", "accident case settle immediately", "do not inform family"],
    ),
    "kyc-expiry-bank": (
        [AUTH, URG, LINK, OTP],
        [
            "your kyc will expire today",
            "account will be blocked",
            "click the link to update kyc",
            "share the otp received",
        ],
    ),
    "courier-drug-package": (
        [AUTH, FEAR, CASE, CAM, ISO, SAFE],
        ["courier with drugs in your name", "narcotics case registered", "stay on video call"],
    ),
    "sim-misuse-trai": (
        [AUTH, FEAR, URG, DOC, CAM],
        [
            "your sim is used for illegal activity",
            "mobile number will be disconnected in two hours",
        ],
    ),
    "remote-access-refund": (
        [AUTH, APP, OTP, SAFE],
        ["install the support app to process refund", "enter the code shown on screen"],
    ),
    "electricity-bill-disconnection": (
        [AUTH, URG, LINK, FEE],
        ["power will be disconnected tonight", "update bill via this link", "pay pending amount"],
    ),
    "court-summons-fine": (
        [AUTH, CASE, FEAR, FEE, URG],
        ["court summons issued against you", "pay fine to avoid warrant", "case number"],
    ),
    "income-tax-notice": (
        [AUTH, CASE, FEAR, DOC, FEE],
        ["income tax notice for unpaid tax", "pay penalty to close the case"],
    ),
    "investment-task-fraud": (
        [LINK, FEE, URG, OTP],
        ["join our trading group", "deposit to unlock profit", "limited time offer"],
    ),
    "lottery-processing-fee": (
        [FEE, URG, DOC, OTP],
        ["you have won a prize", "pay processing fee to release the amount"],
    ),
    "aadhaar-suspension": (
        [AUTH, FEAR, DOC, ISO, URG],
        ["your aadhaar will be suspended", "verify your documents now", "keep this confidential"],
    ),
    "bank-fraud-department": (
        [AUTH, URG, OTP, SAFE],
        ["suspicious transaction on your card", "move funds to a secure account", "share the pin"],
    ),
}


async def seed_scripts(db: AsyncSession) -> int:
    """Idempotently insert seed scripts. Returns number inserted."""
    existing = set((await db.scalars(select(ScamScript.name))).all())
    n = 0
    for name, (seq, phrases) in SEED_SCRIPTS.items():
        if name in existing:
            continue
        s = ScamScript(name=name, tactic_sequence=seq, phrases=phrases, seen_count=0, is_seed=True)
        db.add(s)
        await db.flush()
        await fts_upsert(db, s)
        n += 1
    await db.commit()
    return n
