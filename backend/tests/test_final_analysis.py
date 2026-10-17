import json

from app.actions.report_fields import build_narrative
from app.analysis.final import run_final_analysis
from app.config import Settings
from app.llm.client import LLMClient
from app.llm.usage import UsageTracker
from app.orchestrator import Orchestrator
from app.shield import ShieldAnalyzer

ANALYSIS = {
    "summary": "A fictional caller used a digital-arrest script.",
    "modus_operandi": ["Impersonated an officer", "Demanded a transfer"],
    "narrative": "I received a call from a person claiming to be an officer. I request registration of this complaint.",
    "recommendations": ["Hang up", "Call 1930"],
}


def make_llm(seen: list | None = None) -> LLMClient:
    def handler(tier, msgs):
        if seen is not None:
            seen.append((tier, msgs))
        system = msgs[0]["content"]
        if tier == "deep":
            return json.dumps(ANALYSIS)
        if "Extract identifiers" in system:
            return '{"items": []}'
        if "tag social-engineering" in system or "security classifier" in system:
            return '{"tactics": [], "stage": "contact", "language": "en"}'
        return "Beta, zara dheere boliye."

    s = Settings(_env_file=None, model_fast="f", model_mid="m", model_deep="d")
    return LLMClient(s, UsageTracker(), handler)


async def test_deep_tier_is_called_once_and_sees_only_sanitized_text():
    seen: list = []
    llm = make_llm(seen)
    sm = await Orchestrator(llm=llm, seed=1).run("digital-arrest-parcel", "honeypot", 6)
    deep_calls = [m for t, m in seen if t == "deep"]
    assert len(deep_calls) == 1 and sm.final_analysis and sm.final_analysis["tier"] == "deep"
    user = next(m["content"] for m in deep_calls[0] if m["role"] == "user")
    assert "<untrusted_utterance>" in user
    assert "simverify@examplebank" not in user and "90000 00481" not in user  # identifiers masked
    d = sm.complaint_data()
    assert d.final_analysis and "Analysis summary" in __import__(
        "app.actions.complaint", fromlist=["x"]
    ).build_markdown(d)
    assert build_narrative(d).endswith(ANALYSIS["narrative"])
    assert build_narrative(d).startswith("[SIMULATION")


async def test_no_llm_or_failure_falls_back_to_none():
    assert await run_final_analysis(None, [{"speaker": "scammer", "text": "hi"}], [], False) is None

    def bad(tier, msgs):
        return "not json"

    llm = LLMClient(Settings(_env_file=None, model_deep="d"), UsageTracker(), bad)
    assert await run_final_analysis(llm, [{"speaker": "scammer", "text": "hi"}], [], False) is None


async def test_shield_runs_deep_analysis_on_finish(tmp_path):
    from cryptography.fernet import Fernet

    from app.memory import repo
    from app.memory.crypto import Cipher
    from app.memory.db import init_db, make_engine, make_sessionmaker
    from app.memory.models import Incident

    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path / 'f.db'}")
    await init_db(engine)
    async with make_sessionmaker(engine)() as db:
        u = await repo.get_or_create_user(db)
        await db.commit()
        sh = ShieldAnalyzer(
            make_llm(),
            session_id="s1",
            db=db,
            cipher=Cipher(Fernet.generate_key().decode()),
            user_id=u.id,
        )
        await sh.feed("You are under digital arrest, do not tell anyone", "caller")
        res = await sh.finish()
        inc = await db.get(Incident, res.incident_id)
        assert inc.data["final_analysis"]["summary"] == ANALYSIS["summary"]
    await engine.dispose()
