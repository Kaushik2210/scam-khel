from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    language: Mapped[str] = mapped_column(String(8), default="en")
    client_key: Mapped[str | None] = mapped_column(
        String(64), unique=True, index=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class FamilyMember(Base):
    __tablename__ = "family_members"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    label: Mapped[str] = mapped_column(String(32))  # pseudonym, e.g. FAMILY_1
    role: Mapped[str] = mapped_column(String(32), default="family")
    join_code: Mapped[str] = mapped_column(String(16), unique=True)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(32), default=None)


class ConsentRecord(Base):
    __tablename__ = "consent_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    notice_version: Mapped[str] = mapped_column(String(16))
    purposes: Mapped[list[str]] = mapped_column(JSON)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)


class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    mode: Mapped[str] = mapped_column(String(16))  # shield | honeypot | parent
    scenario: Mapped[str | None] = mapped_column(String(64), default=None)
    language: Mapped[str] = mapped_column(String(8), default="en")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    risk_peak: Mapped[int] = mapped_column(Integer, default=0)
    time_wasted_s: Mapped[int] = mapped_column(Integer, default=0)


class Utterance(Base):
    __tablename__ = "utterances"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), index=True)
    turn: Mapped[int] = mapped_column(Integer)
    speaker: Mapped[str] = mapped_column(String(16))  # scammer | victim | persona
    text_enc: Mapped[str] = mapped_column(Text)  # Fernet token, never plaintext
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    tactics_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    risk_after: Mapped[int] = mapped_column(Integer, default=0)


class EvidenceItem(Base):
    __tablename__ = "evidence_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), index=True)
    type: Mapped[str] = mapped_column(String(32))
    value: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    utterance_id: Mapped[int | None] = mapped_column(ForeignKey("utterances.id"), default=None)


class ScamScript(Base):
    __tablename__ = "scam_scripts"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(96), unique=True)
    tactic_sequence: Mapped[list[str]] = mapped_column(JSON)
    phrases: Mapped[list[str]] = mapped_column(JSON, default=list)
    seen_count: Mapped[int] = mapped_column(Integer, default=0)
    is_seed: Mapped[bool] = mapped_column(Boolean, default=False)
    first_incident_id: Mapped[int | None] = mapped_column(Integer, default=None)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Incident(Base):
    __tablename__ = "incidents"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), index=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    recognised_script_id: Mapped[int | None] = mapped_column(
        ForeignKey("scam_scripts.id"), default=None
    )
    detect_turn: Mapped[int | None] = mapped_column(Integer, default=None)  # risk reached `high`
    memory_hit_turn: Mapped[int | None] = mapped_column(Integer, default=None)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)  # timeline, verifications...
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), index=True)
    pdf_path: Mapped[str | None] = mapped_column(Text, default=None)
    md: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AlertLog(Base):
    __tablename__ = "alert_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    session_id: Mapped[str | None] = mapped_column(String(36), default=None)
    level: Mapped[str] = mapped_column(String(16))
    channel: Mapped[str] = mapped_column(String(16), default="telegram")
    dedupe_key: Mapped[str] = mapped_column(String(96), index=True)
    ok: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class UsageLog(Base):
    __tablename__ = "usage_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    model_tier: Mapped[str] = mapped_column(String(8))
    model: Mapped[str] = mapped_column(String(128), default="")
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
