"""WebSocket live sessions: Shield streaming, honeypot autoplay/manual, replay fallback."""

from __future__ import annotations

import asyncio
import contextlib
import json
import secrets
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.helpers import flush_usage, make_alert_hook
from app.api.state import AppState, LiveSession
from app.guards.demo_mode import first_replay, load_replay
from app.logging import get_logger
from app.memory.models import User
from app.orchestrator import Orchestrator
from app.shield import ShieldAnalyzer

log = get_logger("ws")
router = APIRouter()
MAX_MSG = 4000


class Channel:
    """Send wrapper: swallows send errors after disconnect and enforces the live budget."""

    def __init__(self, ws: WebSocket, st: AppState, live: LiveSession, replay: bool = False):
        self.ws, self.st, self.live, self.replay = ws, st, live, replay
        self.open = True
        self.notified = False

    async def send(self, type_: str, payload: dict[str, Any]) -> None:
        if not self.open:
            return
        try:
            await self.ws.send_json(
                {**payload, "type": type_, **({"replay": True} if self.replay else {})}
            )
        except Exception:
            self.open = False
            self.live.stop.set()
            return
        if not self.replay and self.st.budget.exhausted and not self.notified:
            self.notified = True
            await self.send(
                "budget_notice",
                {
                    "message": "Daily demo budget reached. This session "
                    "will stop; recorded replays remain available."
                },
            )
            self.live.stop.set()


async def _run_replay(ch: Channel, scenario: str) -> None:
    data = load_replay(scenario) or first_replay()
    if data is None:
        await ch.send("budget_notice", {"message": "Budget exhausted and no replay is available."})
        return
    await ch.send(
        "budget_notice",
        {
            "message": "Daily demo budget reached. Showing a recorded replay (not live).",
            "replay_source": data.get("source", "unknown"),
            "scenario": data["scenario"],
        },
    )
    for ev in data["events"]:
        if ch.live.stop.is_set() or not ch.open:
            break
        await ch.send(ev["type"], {k: v for k, v in ev.items() if k != "type"})
        await asyncio.sleep(0.5 if ev["type"] in ("persona_reply", "transcript") else 0.1)


@router.websocket("/ws/sessions/{sid}")
async def session_ws(ws: WebSocket, sid: str, ticket: str = "") -> None:
    st: AppState = ws.app.state.s
    origin = ws.headers.get("origin")
    if (
        origin
        and origin != st.settings.frontend_origin
        and not origin.startswith("http://localhost")
    ):
        await ws.close(code=4403)
        return
    live = st.live.get(sid)
    # The URL carries a per-session ticket, never the long-lived client ID.
    if live is None or not _ticket_ok(ticket, live.ticket):
        await ws.close(code=4404)
        return
    async with st.sm() as db:
        user = await db.get(User, live.user_id)
    if user is None:
        await ws.close(code=4404)
        return
    await ws.accept()
    ch = Channel(ws, st, live)
    task: asyncio.Task[None] | None = None
    shield: ShieldAnalyzer | None = None
    try:
        if live.mode != "shield" and st.budget.exhausted:
            ch.replay = True
            await _run_replay(ch, live.scenario)
            await ch.send("summary", {"replay": True, "ended_reason": "replay_complete"})
            return
        if live.mode == "shield":
            llm = None if st.budget.exhausted else st.llm
            async with st.sm() as db:
                shield = ShieldAnalyzer(
                    llm,
                    ch.send,
                    make_alert_hook(st, user.id, ch.send, False),
                    sid,
                    db=db,
                    cipher=st.cipher,
                    user_id=user.id,
                    language=live.language,
                )
                await _shield_loop(ws, shield, live, ch)
        else:
            task = await _honeypot_loop(ws, st, live, ch, user)
    except WebSocketDisconnect:
        pass
    finally:
        live.stop.set()
        await live.inbox.put(None)
        if task is not None:
            with contextlib.suppress(Exception):
                await asyncio.wait_for(task, 10)
        await flush_usage(st)
        with contextlib.suppress(Exception):
            await ws.close()


def _ticket_ok(given: str, expected: str) -> bool:
    if not given or not expected:
        return False
    return secrets.compare_digest(given.encode("utf-8"), expected.encode("utf-8"))


async def _recv(ws: WebSocket) -> dict[str, Any] | None:
    raw = await ws.receive_text()
    if len(raw) > MAX_MSG:
        await ws.send_json({"type": "error", "message": "message too large"})
        return None
    try:
        msg = json.loads(raw)
    except ValueError:
        await ws.send_json({"type": "error", "message": "invalid JSON"})
        return None
    return msg if isinstance(msg, dict) else None


async def _shield_loop(ws: WebSocket, sh: ShieldAnalyzer, live: LiveSession, ch: Channel) -> None:
    while not live.stop.is_set():
        msg = await _recv(ws)
        if msg is None:
            continue
        kind = msg.get("type")
        if kind == "utterance" and isinstance(msg.get("text"), str) and msg["text"].strip():
            await sh.feed(
                msg["text"].strip()[:2000], "victim" if msg.get("speaker") == "victim" else "caller"
            )
        elif kind == "audio_chunk":
            await ws.send_json(
                {"type": "error", "message": "Streaming audio is not enabled; send text."}
            )
        elif kind == "control" and msg.get("action") in ("stop", "end"):
            break
    res = await sh.finish()
    live.summary = {
        "risk_peak": res.score,
        "level": res.level,
        "incident_id": res.incident_id,
        "detect_turn": res.detect_turn,
        "memory_hit": res.memory_hit,
        "session_id": live.id,
    }
    await ch.send("summary", live.summary)


async def _honeypot_loop(
    ws: WebSocket, st: AppState, live: LiveSession, ch: Channel, user: User
) -> asyncio.Task[None] | None:
    task: asyncio.Task[None] | None = None
    max_turns = min(30, st.settings.max_turns_per_session) if st.settings.demo_mode else 30
    while not live.stop.is_set():
        msg = await _recv(ws)
        if msg is None:
            continue
        kind, action = msg.get("type"), msg.get("action")
        if kind == "control" and action == "start" and task is None:
            speed = max(1, min(8, int(msg.get("speed", 1) or 1)))
            task = asyncio.create_task(
                _run_orchestrator(st, live, ch, user, max_turns, 1.2 / speed)
            )
        elif kind == "control" and action in ("takeover", "stop", "end"):
            live.stop.set()
            await live.inbox.put(None)
        elif kind == "utterance" and isinstance(msg.get("text"), str):
            await live.inbox.put(msg["text"].strip()[:1000])
        elif kind == "audio_chunk":
            await ws.send_json(
                {"type": "error", "message": "Streaming audio is not enabled; send text."}
            )
        if task is not None and task.done():
            break
    return task


async def _run_orchestrator(
    st: AppState, live: LiveSession, ch: Channel, user: User, max_turns: int, pace: float
) -> None:
    async with st.sm() as db:
        orch = Orchestrator(
            llm=None if st.budget.exhausted else st.llm,
            db=db,
            cipher=st.cipher,
            emit=ch.send,
            alert_hook=make_alert_hook(st, user.id, ch.send, True),
            user_id=user.id,
            verifier=st.verifier,
            language=live.language,
        )

        async def victim() -> str | None:
            return await live.inbox.get()

        try:
            sm = await orch.run(
                live.scenario,
                "manual" if live.mode == "manual" else "honeypot",
                max_turns,
                victim_provider=victim if live.mode == "manual" else None,
                stop=live.stop,
                pace_s=pace,
                session_id=live.id,
            )
            live.summary = {
                "risk_peak": sm.risk_peak,
                "level": sm.level,
                "incident_id": sm.incident_id,
                "time_wasted_s": sm.time_wasted_s,
                "session_id": live.id,
            }
        except Exception:
            log.exception("session_failed")
            await ch.send(
                "error", {"message": "The session hit an internal error and was stopped."}
            )
