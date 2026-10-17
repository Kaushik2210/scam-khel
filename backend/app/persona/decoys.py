"""Fixed, clearly fictional decoy data. The honeypot persona may use ONLY these values."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Decoy:
    name: str = "Savitri Devi"
    age: int = 72
    son_name: str = "Raju"
    bank: str = "Nowhere Example Bank"
    upi: str = "decoy@examplebank"
    account: str = "9999-DECOY-0001"  # contains letters: can never be a real account number
    ifsc: str = "EXMP0DECOY1"
    city: str = "Exampleabad"


DECOY = Decoy()

ALLOWED_UPI = {DECOY.upi.lower()}
ALLOWED_IFSC = {DECOY.ifsc.upper()}
ALLOWED_TOKENS = ALLOWED_UPI | {DECOY.account.lower(), DECOY.ifsc.lower()}
