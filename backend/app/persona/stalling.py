"""Stalling library + policy: maximise engaged turns while eliciting scammer identifiers."""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Move:
    id: str
    elicits: str | None  # evidence type this move tries to draw out
    lines: tuple[str, ...]
    pause_s: int  # simulated seconds the stall consumes


MOVES: tuple[Move, ...] = (
    Move(
        "ask_name",
        "officer_name",
        (
            "Beta, aapka poora naam kya hai? Main likh leti hoon, thoda dheere boliye.",
            "Ji, aap kaun bol rahe hain? Naam dobara bataiye, kaan mein kam sunai deta hai.",
        ),
        25,
    ),
    Move(
        "ask_badge",
        "badge_id",
        (
            "Aapka badge number kya hai beta? Mere bete ne kaha tha hamesha pooch lena.",
            "Pehle apna ID number bataiye, main chashma lagake pencil se likhti hoon.",
        ),
        30,
    ),
    Move(
        "ask_callback",
        "phone",
        (
            "Aapka phone number bataiye, main apne bete se baat karke wapas call karti hoon.",
            "Callback number dijiye, line kat gayi toh main kaise phone karungi?",
        ),
        25,
    ),
    Move(
        "ask_office",
        "agency",
        (
            "Aapka office kahan hai? Poora pata bataiye, main Raju ko bata dungi.",
            "Kaun sa department hai aapka? Spelling bataiye, main copy mein likh rahi hoon.",
        ),
        25,
    ),
    Move(
        "ask_written",
        "url",
        (
            "Koi likhit notice bhejiye na, main padh ke samajh lungi. Kahan bhejenge?",
            "Mujhe kaagaz par chahiye, website ka naam bataiye jahan se main dekh sakun.",
        ),
        20,
    ),
    Move(
        "ask_payee",
        "upi",
        (
            "Kis ke naam par bhejna hai? Poora naam aur number ek ek karke bataiye.",
            "Kaun sa account hai? Mujhe likhna padta hai, dheere dheere bataiye.",
        ),
        30,
    ),
    Move(
        "ask_case",
        "case_id",
        ("Mere naam par kaun sa case hai? Case number bataiye, main file mein rakh lungi.",),
        20,
    ),
    Move(
        "glasses",
        None,
        (
            "Ruko beta, mera chashma nahi mil raha. Ek minute...",
            "Arre, chashma kahin rakh diya. Dhoondhne do, line par rahiye.",
        ),
        45,
    ),
    Move(
        "son",
        None,
        (
            "Raju abhi bazaar gaya hai, uska phone mere paas nahi. Thodi der ruk sakte hain?",
            "Main apne bete ko bulati hoon, woh sab samajhta hai. Ruko zara.",
        ),
        40,
    ),
    Move(
        "battery",
        None,
        ("Phone ki battery kam hai beta, charger dhoondh rahi hoon. Hello? Awaaz aa rahi hai?",),
        35,
    ),
    Move(
        "repeat",
        None,
        (
            "Kya kaha? Zara dheere dheere phir se boliye, mujhe samajh nahi aa raha.",
            "Beta, itna tez mat boliye. Ek baar phir se samjhaiye, bilkul shuru se.",
        ),
        30,
    ),
    Move(
        "app_trouble",
        None,
        (
            "Yeh app-wap mujhse nahi khulta beta, mujhe samajh nahi aa raha. Kaise karte hain?",
            "Mere phone mein jagah nahi hai, kuch install nahi hota. Aur koi tareeka hai?",
        ),
        35,
    ),
    Move(
        "worry",
        None,
        ("Hai Ram, mujhe bahut ghabrahat ho rahi hai. Paani pi leti hoon, ek minute.",),
        30,
    ),
)

BY_ID = {m.id: m for m in MOVES}
SAFE_FALLBACK = tuple(line for m in MOVES if m.elicits is None for line in m.lines)


def choose_move(have: set[str], recent: list[str], rng: random.Random, turn: int) -> Move:
    """Prefer moves that elicit identifiers we still lack; interleave pure stalls so the
    conversation stays long and natural; never repeat any of the last three moves."""
    banned = set(recent[-3:])
    missing = [m for m in MOVES if m.elicits and m.elicits not in have and m.id not in banned]
    pure = [m for m in MOVES if m.elicits is None and m.id not in banned]
    # alternate: eliciting move on even turns (if any missing), stalling on odd turns
    if missing and (turn % 2 == 0 or not pure):
        return rng.choice(missing)
    pool = pure or [m for m in MOVES if m.id not in banned] or list(MOVES)
    return rng.choice(pool)


def safe_stall_line(rng: random.Random) -> str:
    """Guaranteed-clean replacement line (contains no digits, links or identifiers)."""
    return rng.choice(SAFE_FALLBACK)


def simulated_seconds(scammer_text: str, persona_text: str, move: Move | None) -> int:
    """Time the scammer wastes this exchange: reading/speaking both sides + the stall pause."""
    scammer_s = len(scammer_text.split()) / 2.2
    persona_s = len(persona_text.split()) / 1.6  # slow, halting speaker
    return round(scammer_s + persona_s + (move.pause_s if move else 15))
