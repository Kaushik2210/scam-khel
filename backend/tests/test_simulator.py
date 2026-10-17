import pytest
from cryptography.fernet import Fernet

from app.evidence.extractor import EvidenceStore
from app.evidence.regexes import extract_candidates
from app.memory import repo
from app.memory.crypto import Cipher
from app.memory.db import init_db, make_engine, make_sessionmaker
from app.orchestrator import Orchestrator
from app.persona.output_guard import find_violations
from app.simulator.scenario import list_scenarios, load_scenario

ALL_IDS = [s.id for s in list_scenarios()]


def test_seven_scenarios_all_labelled_simulation():
    assert len(ALL_IDS) >= 7 and "adversarial-injection" in ALL_IDS
    for s in list_scenarios():
        assert "(SIMULATION)" in s.agency
        for st in s.stages:
            for line in st.lines:
                s.render(line)  # all placeholders resolvable


def test_unknown_scenario_and_path_traversal_rejected():
    for bad in ("nope", "../config"):
        with pytest.raises(KeyError):
            load_scenario(bad)


def test_evidence_regexes_cover_many_types():
    text = (
        "Inspector Rao here, badge number SIM-48213. Case number NCV-48213. Call +91 90000 00481, "
        "pay Rs 2,40,000 within 2 hours to simverify@examplebank, account SIM00004821300, "
        "IFSC EXMP0SIM001, see https://verify.example.test/case or get fake.apk. "
        "National Crime Verification Cell (SIMULATION)"
    )
    got = {c.type for c in extract_candidates(text)}
    assert {
        "phone",
        "upi",
        "ifsc",
        "account",
        "url",
        "apk",
        "badge_id",
        "case_id",
        "officer_name",
        "amount",
        "deadline",
        "agency",
    } <= got


async def test_evidence_dedupes_and_raises_confidence():
    s = EvidenceStore()
    new1 = await s.ingest("Pay to simverify@examplebank now", 1)
    new2 = await s.ingest("I repeat simverify@examplebank", 2)
    assert len(new1) == 1 and new2 == []
    rec = next(r for r in s.items() if r.type == "upi")
    assert rec.mentions == 2 and rec.confidence > 0.7 and rec.turn == 1


@pytest.mark.parametrize("sid", ALL_IDS)
async def test_autoplay_completes_with_zero_leakage(sid):
    events = []

    async def emit(t, p):
        events.append(t)

    sm = await Orchestrator(emit=emit, seed=1).run(sid, "honeypot", max_turns=14)
    assert sm.scammer_turns >= 5 and sm.persona_turns >= 4
    assert sm.risk_peak >= 85 and sm.level == "critical"
    assert sm.time_wasted_s > 60
    for t in sm.transcript:
        if t["speaker"] == "persona":
            assert find_violations(t["text"]) == [], t["text"]
    assert {"transcript", "tactics", "risk", "persona_reply", "evidence", "summary"} <= set(events)
    assert len({e["type"] for e in sm.evidence}) >= 5


async def test_adversarial_scenario_neutralised():
    sm = await Orchestrator(seed=2).run("adversarial-injection", "honeypot", max_turns=12)
    assert sm.injection_attempts >= 2
    persona = [t["text"] for t in sm.transcript if t["speaker"] == "persona"]
    assert persona and all(find_violations(t) == [] for t in persona)
    assert all("ai" not in t.lower().split() for t in persona)


async def test_user_takeover_stops_persona():
    async def victim():
        return None  # user takes over immediately

    sm = await Orchestrator(seed=1).run("fake-customs", "honeypot", 10, victim_provider=victim)
    assert sm.ended_reason == "user_takeover" and sm.persona_turns == 0


async def test_scammer_disengages_after_patience():
    sm = await Orchestrator(seed=1).run("fake-customs", "honeypot", max_turns=40)
    assert sm.ended_reason == "scammer_disengaged"


async def test_alert_hook_fires_once_per_level():
    calls = []

    async def hook(level, payload):
        calls.append(level)

    await Orchestrator(alert_hook=hook, seed=1).run("digital-arrest-parcel", "honeypot", 8)
    assert calls and len(calls) == len(set(calls)) and "critical" in calls


# --- the memory benefit, end to end through the orchestrator -----------------------------------


@pytest.fixture
async def db(tmp_path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path / 'o.db'}")
    await init_db(engine)
    async with make_sessionmaker(engine)() as s:
        yield s
    await engine.dispose()


async def test_second_exposure_is_flagged_no_later_and_persisted(db):
    cipher = Cipher(Fernet.generate_key().decode())
    u = await repo.get_or_create_user(db)
    await db.commit()
    first = await Orchestrator(db=db, cipher=cipher, user_id=u.id, seed=1).run(
        "kyc-expiry-bank", "honeypot", 8
    )
    assert first.memory_hit is None and first.incident_id
    second = await Orchestrator(db=db, cipher=cipher, user_id=u.id, seed=1).run(
        "kyc-expiry-bank", "honeypot", 8
    )
    assert second.memory_hit is not None
    assert second.memory_hit["earlier_incident_id"] == first.incident_id
    assert second.detect_turn is not None and first.detect_turn is not None
    assert second.detect_turn <= first.detect_turn
    # utterances stored encrypted, retrievable
    rows = await repo.get_utterances(db, cipher, first.session_id)
    assert rows and any("KYC" in text for _, text in rows)
