"""Tactic taxonomy. P1 extends each entry with EN/HI/Hinglish keyword rules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tactic:
    id: str
    description: str
    severity: int  # 1 (low) .. 10 (critical)


TACTICS: dict[str, Tactic] = {
    t.id: t
    for t in [
        Tactic("authority_impersonation", "Claims to be police/CBI/ED/customs/bank official", 5),
        Tactic("fear_arrest_threat", "Threatens arrest, case, seizure or account freeze", 7),
        Tactic("isolation_secrecy", "Tells the victim not to tell anyone", 8),
        Tactic(
            "stay_on_camera_digital_arrest", "Demands the victim stay visible on a video call", 9
        ),
        Tactic("urgency_deadline", "Imposes an immediate deadline", 4),
        Tactic("fake_case_or_badge_id", "Quotes a case number, FIR or badge ID", 4),
        Tactic("document_demand", "Asks for Aadhaar, PAN or bank details", 6),
        Tactic("safe_account_transfer", "Asks to move money to a 'safe/verification account'", 10),
        Tactic("verification_fee_or_deposit", "Demands a fee, fine or deposit", 9),
        Tactic("remote_access_app_request", "Asks to install a remote-access app", 9),
        Tactic("otp_request", "Asks for an OTP or PIN", 9),
        Tactic("link_or_apk_push", "Pushes a link or APK download", 7),
        Tactic("family_member_implicated", "Claims a family member is involved in a crime", 6),
    ]
}


def is_valid_tactic(tactic_id: str) -> bool:
    return tactic_id in TACTICS
