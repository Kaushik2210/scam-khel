from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Lang = Literal["en", "hi", "hinglish"]


class SessionIn(BaseModel):
    mode: Literal["shield", "honeypot", "manual"]
    scenario: str = Field("digital-arrest-parcel", max_length=64, pattern=r"^[a-z0-9\-]+$")
    language: Lang = "en"
    consent: bool


class TurnIn(BaseModel):
    s: Literal["caller", "victim"] = "caller"
    t: str = Field(max_length=2000)


class AnalyzeIn(BaseModel):
    text: str | None = Field(None, max_length=8000)
    turns: list[TurnIn] | None = Field(None, max_length=60)
    language: Lang = "en"
    consent: bool


class FamilyIn(BaseModel):
    label: str = Field(min_length=1, max_length=32)
    role: str = Field("family", max_length=32)


class PanicIn(BaseModel):
    language: Lang = "en"
    session_id: str | None = Field(None, max_length=36)
    amount_inr: float = Field(gt=0, le=1e10)
    txn_date: str | None = Field(None, max_length=10)
    txn_time: str | None = Field(None, max_length=8)
    mode: Literal["upi", "neft_imps_rtgs", "card", "cash", "other"] = "upi"
    beneficiary_name: str = Field("", max_length=120)
    beneficiary_account_or_upi: str = Field("", max_length=64)
    bank_name: str = Field("", max_length=80)
    txn_reference: str = Field("", max_length=64)
    caller_phone: str = Field("", max_length=20)


class FeedbackIn(BaseModel):
    verdict: Literal["scam", "not_scam"]
    notes: str = Field("", max_length=500)
