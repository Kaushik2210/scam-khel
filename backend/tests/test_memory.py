from datetime import timedelta

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import select, text

from app.memory import repo
from app.memory.crypto import Cipher, CryptoError
from app.memory.db import init_db, make_engine, make_sessionmaker
from app.memory.learn import LearnTurn, learn_session
from app.memory.models import Incident, ScamScript, Session, Utterance, utcnow
from app.memory.retrieval import fts_scores, normalise_phrase, recognize
from app.memory.scripts import SEED_SCRIPTS, seed_scripts


@pytest.fixture
async def db(tmp_path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path / 't.db'}")
    await init_db(engine)
    async with make_sessionmaker(engine)() as s:
        yield s
    await engine.dispose()


@pytest.fixture
def cipher():
    return Cipher(Fernet.generate_key().decode())


async def mk_session(db, user_id, sid="s1", started=None):
    s = Session(id=sid, user_id=user_id, mode="honeypot")
    if started:
        s.started_at = started
    db.add(s)
    await db.flush()
    return s


# --- crypto ---------------------------------------------------------------


def test_cipher_roundtrip_and_errors():
    c = Cipher(Fernet.generate_key().decode())
    tok = c.encrypt("नमस्ते digital arrest")
    assert "arrest" not in tok and c.decrypt(tok) == "नमस्ते digital arrest"
    with pytest.raises(CryptoError):
        Cipher("")
    with pytest.raises(CryptoError):
        Cipher("not-a-key")
    with pytest.raises(CryptoError):
        Cipher(Fernet.generate_key().decode()).decrypt(tok)


async def test_utterance_text_is_encrypted_at_rest(db, cipher):
    u = await repo.get_or_create_user(db)
    await mk_session(db, u.id)
    await repo.add_utterance(
        db, cipher, session_id="s1", turn=1, speaker="scammer", text_plain="send money now"
    )
    await db.commit()
    raw = (await db.execute(text("SELECT text_enc FROM utterances"))).scalar_one()
    assert "send money" not in raw
    rows = await repo.get_utterances(db, cipher, "s1")
    assert rows[0][1] == "send money now"


# --- seeding / retrieval ---------------------------------------------------


async def test_seed_idempotent_and_at_least_15(db):
    assert len(SEED_SCRIPTS) >= 15
    assert await seed_scripts(db) == len(SEED_SCRIPTS)
    assert await seed_scripts(db) == 0


async def test_seed_recognition_and_fts(db):
    await seed_scripts(db)
    hit = await recognize(
        db,
        ["authority_impersonation", "fake_case_or_badge_id", "fear_arrest_threat"],
        "parcel in your name contains illegal items",
    )
    assert hit and hit.script_name == "digital-arrest-parcel"
    assert hit.earlier_incident_id is None and "known script" in hit.banner()
    scores = await fts_scores(db, "pay the clearance fee for customs")
    names = {
        (await db.get(ScamScript, i)).name
        for i in scores  # type: ignore[union-attr]
    }
    assert "fake-customs-parcel" in names


async def test_no_hit_below_prefix_length_or_unrelated(db):
    await seed_scripts(db)
    assert await recognize(db, ["authority_impersonation", "fear_arrest_threat"]) is None
    assert (
        await recognize(db, ["otp_request", "link_or_apk_push", "stay_on_camera_digital_arrest"])
        is None
    )


def test_normalise_phrase():
    assert normalise_phrase("Pay Rs. 49,999 NOW!!") == "pay rs <num> <num> now"


# --- the headline metric: second exposure is flagged earlier ----------------

NOVEL = [  # an unseen script (not in seed library)
    ["urgency_deadline"],
    ["link_or_apk_push"],
    ["remote_access_app_request"],
    ["otp_request"],
    ["verification_fee_or_deposit"],
]


async def run_session(db, user_id, sid, detect_turn_by_risk):
    """Simulates the orchestrator loop: after each turn, ask memory whether it's seen this."""
    await mk_session(db, user_id, sid)
    observed: list[str] = []
    hit_turn = None
    hit = None
    for i, tactics in enumerate(NOVEL, 1):
        observed += [t for t in tactics if t not in observed]
        if hit is None:
            h = await recognize(db, observed, hit_turn=i)
            if h:
                hit, hit_turn = h, i
    turns = [LearnTurn("scammer", t, [f"phrase for {t}".replace("_", " ")]) for t in NOVEL]
    inc = await learn_session(
        db,
        session_id=sid,
        turns=turns,
        detect_turn=detect_turn_by_risk,
        memory_hit_turn=hit_turn,
    )
    return inc, hit


async def test_second_exposure_flagged_earlier(db):
    u = await repo.get_or_create_user(db)
    inc1, hit1 = await run_session(db, u.id, "s1", detect_turn_by_risk=5)
    assert hit1 is None  # first exposure: nothing in memory
    assert inc1.recognised_script_id is not None  # ...but it was learned

    inc2, hit2 = await run_session(db, u.id, "s2", detect_turn_by_risk=5)
    assert hit2 is not None and hit2.hit_turn == 3  # 3-tactic prefix on 1st learning
    assert hit2.hit_turn < hit2.earlier_detect_turn
    assert hit2.earlier_incident_id == inc1.id
    assert hit2.banner() == (
        f"Recognised pattern from Incident #{inc1.id} — flagged at turn 3 vs turn 5 earlier"
    )
    script = await db.get(ScamScript, inc2.recognised_script_id)
    assert script.seen_count == 2 and script.first_incident_id == inc1.id

    # priors updated: after 2 sightings a 2-tactic prefix is enough
    _, hit3 = await run_session(db, u.id, "s3", detect_turn_by_risk=5)
    assert hit3.hit_turn == 2


async def test_unrelated_session_makes_new_script(db):
    u = await repo.get_or_create_user(db)
    await run_session(db, u.id, "s1", 5)
    await mk_session(db, u.id, "s2")
    await learn_session(
        db,
        session_id="s2",
        turns=[
            LearnTurn("scammer", ["authority_impersonation"]),
            LearnTurn("scammer", ["fear_arrest_threat"]),
            LearnTurn("scammer", ["isolation_secrecy"]),
        ],
        detect_turn=2,
    )
    assert len((await db.scalars(select(ScamScript))).all()) == 2


async def test_weak_signal_creates_incident_but_no_script(db):
    u = await repo.get_or_create_user(db)
    await mk_session(db, u.id)
    inc = await learn_session(
        db, session_id="s1", turns=[LearnTurn("scammer", ["urgency_deadline"])], detect_turn=None
    )
    assert inc.recognised_script_id is None
    assert (await db.scalars(select(ScamScript))).all() == []


# --- privacy: consent, retention, delete -----------------------------------


async def test_consent_gate(db):
    u = await repo.get_or_create_user(db)
    assert not await repo.has_consent(db, u.id)
    await repo.record_consent(db, u.id)
    assert await repo.has_consent(db, u.id)


async def test_purge_only_removes_old(db, cipher):
    u = await repo.get_or_create_user(db)
    await mk_session(db, u.id, "old", started=utcnow() - timedelta(days=40))
    await mk_session(db, u.id, "new")
    for sid in ("old", "new"):
        await repo.add_utterance(
            db, cipher, session_id=sid, turn=1, speaker="scammer", text_plain="x"
        )
    await db.commit()
    assert await repo.purge_older_than(db, 30) == 1
    assert [s.id for s in (await db.scalars(select(Session))).all()] == ["new"]
    assert len((await db.scalars(select(Utterance))).all()) == 1


async def test_delete_user_data_removes_everything_personal(db, cipher):
    await seed_scripts(db)
    u = await repo.get_or_create_user(db)
    await repo.record_consent(db, u.id)
    inc, _ = await run_session(db, u.id, "s1", 5)
    await repo.add_utterance(db, cipher, session_id="s1", turn=1, speaker="scammer", text_plain="x")
    await db.commit()
    await repo.delete_user_data(db, u.id)
    for table in ("users", "sessions", "utterances", "incidents", "consent_records"):
        assert (await db.execute(text(f"SELECT COUNT(*) FROM {table}"))).scalar_one() == 0
    # learned script is removed, seed library remains
    names = {s.name for s in (await db.scalars(select(ScamScript))).all()}
    assert names == set(SEED_SCRIPTS)
    assert await db.scalar(select(Incident.id)) is None
