import json

import httpx
import pytest
from sqlalchemy import select

from app.actions.alerts import MAX_ALERTS_PER_HOUR, AlertService, format_alert
from app.actions.panic import TransactionDetails, panic_bundle
from app.actions.telegram import (
    MAX_BAD_CODES,
    TelegramClient,
    TelegramError,
    handle_update,
)
from app.guards.ratelimit import RateLimiter
from app.memory import repo
from app.memory.db import init_db, make_engine, make_sessionmaker
from app.memory.models import AlertLog


class Bot:
    """Mock Telegram Bot API."""

    def __init__(self, fail=False):
        self.sent = []
        self.fail = fail

    def handler(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if self.fail:
            return httpx.Response(401, json={"ok": False, "description": "Unauthorized"})
        self.sent.append((request.url.path.split("/")[-1], body))
        return httpx.Response(200, json={"ok": True, "result": {}})

    def client(self, token="123:SECRET") -> TelegramClient:
        return TelegramClient(token, httpx.AsyncClient(transport=httpx.MockTransport(self.handler)))


@pytest.fixture
async def db(tmp_path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path / 'p5.db'}")
    await init_db(engine)
    async with make_sessionmaker(engine)() as s:
        yield s
    await engine.dispose()


async def family(db, n=2):
    u = await repo.get_or_create_user(db)
    await db.commit()
    ms = [await repo.add_family_member(db, u.id, f"FAMILY_{i}") for i in range(1, n + 1)]
    return u, ms


async def join(db, bot, member, chat):
    tg = bot.client()
    return await handle_update(
        {"message": {"text": f"/start {member.join_code}", "chat": {"id": chat}}}, db, tg
    )


async def test_start_code_links_chat(db):
    bot = Bot()
    _, (m, _) = await family(db)
    assert await join(db, bot, m, 111) == "linked"
    await db.refresh(m)
    assert m.telegram_chat_id == "111"
    assert bot.sent[-1][1]["chat_id"] == "111"
    tg = bot.client()
    assert (
        await handle_update({"message": {"text": "/start nope", "chat": {"id": 5}}}, db, tg)
        == "unknown_code"
    )
    assert (
        await handle_update({"message": {"text": "/start", "chat": {"id": 5}}}, db, tg)
        == "missing_code"
    )
    assert await handle_update({"message": {"text": "hello", "chat": {"id": 5}}}, db, tg) is None


async def test_join_codes_are_long_unambiguous_and_unique(db):
    _, members = await family(db, n=6)
    codes = [m.join_code for m in members]
    assert len(set(codes)) == len(codes)
    for c in codes:
        assert len(c) == repo.JOIN_CODE_LENGTH == 10
        assert set(c) <= set(repo.JOIN_CODE_ALPHABET)
        assert not set(c) & set("01ILOilo")


async def test_code_is_case_insensitive_and_legacy_lowercase_codes_still_work(db):
    bot = Bot()
    _, (m, m2) = await family(db)
    tg = bot.client()

    def upd(code, chat):
        return {"message": {"text": f"/start {code}", "chat": {"id": chat}}}

    assert await handle_update(upd(m.join_code.lower(), 21), db, tg) == "linked"
    m2.join_code = "a1b2c3d4"  # an 8-char lowercase hex code issued before this change
    await db.commit()
    assert await handle_update(upd("A1B2C3D4", 22), db, tg) == "linked"


async def test_linked_slot_cannot_be_taken_over_with_the_same_code(db):
    bot = Bot()
    _, (m, _) = await family(db)
    assert await join(db, bot, m, 111) == "linked"
    assert await join(db, bot, m, 222) == "already_linked"
    await db.refresh(m)
    assert m.telegram_chat_id == "111"
    assert "already in use" in bot.sent[-1][1]["text"]
    assert bot.sent[-1][1]["chat_id"] == "222"
    assert await join(db, bot, m, 111) == "linked"  # the same chat repeating /start is fine


async def test_wrong_codes_lock_a_chat_out_even_for_the_right_code(db):
    bot = Bot()
    limiter = RateLimiter()
    _, (m, _) = await family(db)
    tg = bot.client()

    def upd(code, chat):
        return {"message": {"text": f"/start {code}", "chat": {"id": chat}}}

    for _ in range(MAX_BAD_CODES):
        assert await handle_update(upd("WRONGCODE1", 9), db, tg, limiter) == "unknown_code"
    assert await handle_update(upd(m.join_code, 9), db, tg, limiter) == "rate_limited"
    await db.refresh(m)
    assert m.telegram_chat_id is None
    # another chat is unaffected
    assert await handle_update(upd(m.join_code, 10), db, tg, limiter) == "linked"


async def test_alert_content_dedupe_and_critical_escalation(db):
    bot = Bot()
    u, (m1, m2) = await family(db)
    await join(db, bot, m1, 111)
    await join(db, bot, m2, 222)
    bot.sent.clear()
    svc = AlertService(db, bot.client(), "https://app.example.test/")
    args = dict(
        user_id=u.id,
        session_id="s1",
        tactics=["fear_arrest_threat", "isolation_secrecy"],
        summary="Caller claims to be police.",
        incident_id=7,
        simulation=True,
    )

    r = await svc.send_family_alert(level="high", **args)
    assert r.sent == 2 and len(bot.sent) == 2
    text = bot.sent[0][1]["text"]
    for needle in (
        "[SIMULATION]",
        "HIGH RISK",
        "Call your parent now",
        "1930",
        "https://app.example.test/incidents/7",
        "arrest",
    ):
        assert needle in text
    assert (await svc.send_family_alert(level="high", **args)).skipped == "duplicate"
    assert (await svc.send_family_alert(level="critical", **args)).sent == 2  # escalates once
    assert (await svc.send_family_alert(level="critical", **args)).skipped == "duplicate"
    logs = (await db.scalars(select(AlertLog))).all()
    assert len(logs) == 4 and all(entry.ok for entry in logs)


async def test_rate_limit(db):
    bot = Bot()
    u, (m, _) = await family(db)
    await join(db, bot, m, 1)
    svc = AlertService(db, bot.client(), "https://x.test")
    for i in range(MAX_ALERTS_PER_HOUR):
        assert (await svc.send_family_alert(u.id, f"s{i}", "high", [], "x")).sent == 1
    assert (await svc.send_family_alert(u.id, "sX", "high", [], "x")).skipped == "rate_limited"


async def test_no_recipients_not_configured_and_failure_logged_without_token(db):
    u, _ = await family(db)
    bot = Bot()
    assert (
        await AlertService(db, bot.client(), "x").send_family_alert(u.id, "s", "high", [], "x")
    ).skipped == "no_recipients"
    assert (
        await AlertService(db, TelegramClient(""), "x").send_family_alert(
            u.id, "s", "high", [], "x"
        )
    ).skipped == "not_configured"

    ms = await repo.list_family(db, u.id)
    ms[0].telegram_chat_id = "9"
    await db.commit()
    bad = Bot(fail=True)
    r = await AlertService(db, bad.client(), "x").send_family_alert(u.id, "s2", "high", [], "x")
    assert r.sent == 0 and r.errors == 1
    log = (await db.scalars(select(AlertLog))).all()[-1]
    assert not log.ok
    with pytest.raises(TelegramError) as ei:
        await bad.client().send_message("9", "x")
    assert "SECRET" not in str(ei.value)


def test_format_alert_plain_language():
    t = format_alert(
        "money_sent", ["safe_account_transfer"], "Money may have been sent.", "https://x.test"
    )
    assert "MONEY ALREADY SENT" in t and "safe" in t.lower() and "1930" in t


def test_panic_bundle_en_and_hi():
    tx = TransactionDetails(
        amount_inr=240000,
        beneficiary_account_or_upi="simverify@examplebank",
        bank_name="Example Bank",
    )
    b = panic_bundle(tx)
    assert b["helpline"] == "1930" and "1930" in b["checklist"][0]
    assert "Rs 2,40,000" in b["call_script"] or "Rs 240,000.00" in b["call_script"]
    assert "simverify@examplebank" in b["call_script"]
    assert b["transaction_form"]["Transaction reference"] == "(fill in)"
    assert "DRAFT" in b["complaint_markdown"] and "Transaction details" in b["complaint_markdown"]
    hi = panic_bundle(tx, "hi")
    assert "1930" in hi["checklist"][0] and "नमस्ते" in hi["call_script"]


def test_transaction_validation():
    with pytest.raises(ValueError):
        TransactionDetails(amount_inr=-5)
    with pytest.raises(ValueError):
        TransactionDetails(amount_inr=5, mode="bitcoin")  # type: ignore[arg-type]
