import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

CID = "client-0000-aaaa"
H = {"X-Client-Id": CID}


def make(tmp_path, **kw):
    s = Settings(
        _env_file=None,
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'api.db'}",
        frontend_origin="http://localhost:3000",
        admin_token="adm-secret",
        **kw,
    )
    return create_app(s, fernet_key=Fernet.generate_key().decode(), use_llm=False)


@pytest.fixture
def client(tmp_path):
    with TestClient(make(tmp_path)) as c:
        yield c


def drain(ws, until="summary", limit=400):
    events = []
    for _ in range(limit):
        e = ws.receive_json()
        events.append(e)
        if e["type"] == until:
            break
    return events


def test_health_models_and_security_headers(client):
    r = client.get("/healthz")
    assert r.status_code == 200 and r.json()["llm_mode"] == "offline"
    assert (
        r.headers["x-content-type-options"] == "nosniff" and r.headers["x-frame-options"] == "DENY"
    )
    m = client.get("/api/models/status").json()
    assert set(m["tiers"]) == {"fast", "mid", "deep"} and "Nebius" in m["provider"]
    assert len(client.get("/api/scenarios").json()) >= 7


def test_consent_and_client_id_required(client):
    body = {
        "mode": "shield",
        "scenario": "digital-arrest-parcel",
        "language": "en",
        "consent": False,
    }
    assert client.post("/api/sessions", json=body, headers=H).status_code == 400
    assert client.post("/api/sessions", json={**body, "consent": True}).status_code == 400  # no id
    assert (
        client.post("/api/sessions", json={**body, "consent": True}, headers=H).status_code == 200
    )


def test_validation_and_size_cap(client):
    bad = {"mode": "honeypot", "scenario": "../etc", "language": "en", "consent": True}
    assert client.post("/api/sessions", json=bad, headers=H).status_code == 422
    big = {"text": "x" * 70000, "language": "en", "consent": True}
    assert client.post("/api/analyze", json=big, headers=H).status_code == 413
    nope = {"mode": "honeypot", "scenario": "nope", "language": "en", "consent": True}
    assert client.post("/api/sessions", json=nope, headers=H).status_code == 404


def test_cors_locked_to_frontend(client):
    ok = client.options(
        "/healthz",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
    )
    bad = client.options(
        "/healthz", headers={"Origin": "https://evil.test", "Access-Control-Request-Method": "GET"}
    )
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert "access-control-allow-origin" not in bad.headers


def test_analyze_then_incident_complaint_blocklist_delete(client):
    text = (
        "This is Inspector Rao from the Cyber Crime Branch. Your Aadhaar is linked to money "
        "laundering and a warrant is ready.\nYou are under digital arrest. Do not tell anyone, "
        "stay on the video call.\nTransfer Rs 90,000 to the RBI safe account simverify@examplebank "
        "immediately."
    )
    r = client.post(
        "/api/analyze", json={"text": text, "language": "en", "consent": True}, headers=H
    )
    assert r.status_code == 200
    a = r.json()
    assert a["level"] == "critical" and a["detect_turn"] <= 2 and a["llm_mode"] == "rules-only"
    assert "simverify@examplebank" in {e["value"] for e in a["evidence"]}
    assert a["explanation"]["what_to_do"]

    inc = client.get(f"/api/incidents/{a['incident_id']}", headers=H).json()
    assert len(inc["transcript"]) == 3 and inc["transcript"][0]["text"].startswith(
        "This is Inspector"
    )
    assert client.get("/api/incidents", headers=H).json()[0]["id"] == a["incident_id"]

    md = client.get(f"/api/sessions/{a['session_id']}/complaint.md", headers=H)
    assert md.status_code == 200 and "DRAFT" in md.text and "1930" in md.text
    pdf = client.get(f"/api/sessions/{a['session_id']}/complaint.pdf", headers=H)
    assert pdf.content[:5] == b"%PDF-"
    assert "simverify@examplebank" in client.get("/api/blocklist.csv", headers=H).text
    assert client.get("/api/blocklist.json", headers=H).json()["items"]

    # isolation: another client sees nothing
    other = {"X-Client-Id": "client-9999-bbbb"}
    assert client.get("/api/incidents", headers=other).json() == []
    assert client.get(f"/api/incidents/{a['incident_id']}", headers=other).status_code == 404
    assert (
        client.get(f"/api/sessions/{a['session_id']}/complaint.pdf", headers=other).status_code
        == 404
    )

    assert client.delete("/api/me/data", headers=H).json() == {"deleted": True}
    assert client.get("/api/incidents", headers=H).json() == []


def test_legit_text_stays_low(client):
    r = client.post(
        "/api/analyze",
        headers=H,
        json={
            "text": "Example Bank: Rs 1,250 debited. Never share your OTP or PIN with anyone.",
            "language": "en",
            "consent": True,
        },
    ).json()
    assert r["level"] == "low" and not r["explanation"]["what_to_do"]


def test_second_analyze_hits_memory(client):
    t = (
        "Inspector Rao here, a warrant is ready.\nStay on the video call, do not tell anyone.\n"
        "Send your Aadhaar and bank details now.\nTransfer money to the safe account."
    )
    body = {"text": t, "language": "en", "consent": True}
    one = client.post("/api/analyze", json=body, headers=H).json()
    two = client.post("/api/analyze", json=body, headers=H).json()
    assert two["memory_hit"] and two["memory_hit"]["earlier_incident_id"] == one["incident_id"]


def test_family_flow_and_admin_usage_protected(client):
    assert client.get("/api/family", headers=H).json()["members"] == []
    m = client.post("/api/family", json={"label": "FAMILY_1"}, headers=H).json()
    assert len(m["join_code"]) == 10
    assert client.get("/api/family", headers=H).json()["members"][0]["linked"] is False
    assert client.post("/api/family/test-alert", headers=H).status_code == 503  # no bot token
    assert client.get("/api/admin/usage").status_code == 403
    assert client.get("/api/admin/usage", headers={"X-Admin-Token": "wrong"}).status_code == 403
    u = client.get("/api/admin/usage", headers={"X-Admin-Token": "adm-secret"}).json()
    assert set(u["by_tier"]) >= {"fast", "mid", "deep"}
    assert client.post("/api/telegram/webhook", json={}).status_code == 403


def test_family_member_can_be_removed_only_by_its_owner(client):
    m = client.post("/api/family", json={"label": "FAMILY_1"}, headers=H).json()
    other = {"X-Client-Id": "client-1111-bbbb"}
    assert client.delete(f"/api/family/{m['id']}", headers=other).status_code == 404
    assert len(client.get("/api/family", headers=H).json()["members"]) == 1
    assert client.delete(f"/api/family/{m['id']}", headers=H).json() == {"deleted": True}
    assert client.get("/api/family", headers=H).json()["members"] == []
    assert client.delete(f"/api/family/{m['id']}", headers=H).status_code == 404


def test_panic_endpoint(client):
    r = client.post(
        "/api/panic",
        headers=H,
        json={
            "language": "en",
            "amount_inr": 50000,
            "beneficiary_account_or_upi": "simverify@examplebank",
        },
    )
    assert r.status_code == 200
    b = r.json()
    assert b["helpline"] == "1930" and "simverify@examplebank" in b["call_script"]
    assert client.post("/api/panic", headers=H, json={"amount_inr": -1}).status_code == 422


def test_session_rate_limit(tmp_path):
    with TestClient(make(tmp_path, per_ip_sessions_per_hour=2)) as c:
        body = {
            "mode": "shield",
            "scenario": "digital-arrest-parcel",
            "language": "en",
            "consent": True,
        }
        assert [c.post("/api/sessions", json=body, headers=H).status_code for _ in range(3)] == [
            200,
            200,
            429,
        ]


def test_ws_honeypot_autoplay_end_to_end(client):
    s = client.post(
        "/api/sessions",
        headers=H,
        json={
            "mode": "honeypot",
            "scenario": "digital-arrest-parcel",
            "language": "hinglish",
            "consent": True,
        },
    ).json()
    with client.websocket_connect(f"/ws/sessions/{s['id']}?ticket={s['ws_ticket']}") as ws:
        ws.send_json({"type": "control", "action": "start", "speed": 8})
        ev = drain(ws)
    types = {e["type"] for e in ev}
    assert {"transcript", "tactics", "risk", "persona_reply", "evidence", "summary"} <= types
    final = ev[-1]
    assert final["level"] == "critical" and final["time_wasted_s"] > 60 and final["incident_id"]
    assert all(
        e.get("simulation") for e in ev if e["type"] == "transcript" and e["speaker"] == "scammer"
    )
    pdf = client.get(f"/api/sessions/{s['id']}/complaint.pdf", headers=H)
    assert pdf.status_code == 200 and pdf.content[:5] == b"%PDF-"


def test_ws_manual_takeover_and_shield_streaming(client):
    s = client.post(
        "/api/sessions",
        headers=H,
        json={"mode": "manual", "scenario": "fake-customs", "language": "en", "consent": True},
    ).json()
    with client.websocket_connect(f"/ws/sessions/{s['id']}?ticket={s['ws_ticket']}") as ws:
        ws.send_json({"type": "control", "action": "start", "speed": 8})
        ev = drain(ws, "risk")  # scammer's first line analysed; orchestrator now awaits the victim
        ws.send_json({"type": "utterance", "text": "Who is this?"})
        ev += drain(ws, "risk")  # victim echoed, scammer's second line analysed
        ws.send_json({"type": "control", "action": "takeover"})
        ev += drain(ws)
    assert ev[-1]["ended_reason"] == "user_takeover"
    assert any(e["type"] == "transcript" and e["speaker"] == "victim" for e in ev)

    s2 = client.post(
        "/api/sessions",
        headers=H,
        json={"mode": "shield", "scenario": "x", "language": "en", "consent": True},
    ).json()
    with client.websocket_connect(f"/ws/sessions/{s2['id']}?ticket={s2['ws_ticket']}") as ws:
        ws.send_json(
            {"type": "utterance", "text": "You are under digital arrest, do not tell anyone"}
        )
        e1 = drain(ws, "risk")
        ws.send_json({"type": "audio_chunk", "data": "AAAA"})
        assert drain(ws, "error")[-1]["type"] == "error"
        ws.send_json({"type": "control", "action": "stop"})
        end = drain(ws)
    assert e1[-1]["level"] in ("high", "critical") and end[-1]["type"] == "summary"


def test_ws_rejects_wrong_ticket_client_id_and_unknown_session(client):
    s = client.post(
        "/api/sessions",
        headers=H,
        json={"mode": "shield", "scenario": "x", "language": "en", "consent": True},
    ).json()
    from starlette.websockets import WebSocketDisconnect

    assert s["ws_ticket"] and s["ws_ticket"] != CID
    for url in (
        f"/ws/sessions/{s['id']}?ticket=not-the-ticket",
        f"/ws/sessions/{s['id']}?ticket=",
        f"/ws/sessions/{s['id']}?ticket=café",  # non-ASCII must reject, not crash
        "/ws/sessions/nope?ticket=" + s["ws_ticket"],
        f"/ws/sessions/{s['id']}?client_id={CID}",  # the long-lived ID is no longer accepted
        f"/ws/sessions/{s['id']}",
    ):
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(url):
                pass


def test_ws_ticket_is_per_session_and_not_the_client_id(client):
    mk = lambda: client.post(  # noqa: E731
        "/api/sessions",
        headers=H,
        json={"mode": "shield", "scenario": "x", "language": "en", "consent": True},
    ).json()
    a, b = mk(), mk()
    assert a["ws_ticket"] != b["ws_ticket"]
    from starlette.websockets import WebSocketDisconnect

    with pytest.raises(WebSocketDisconnect):  # session A's ticket does not open session B
        with client.websocket_connect(f"/ws/sessions/{b['id']}?ticket={a['ws_ticket']}"):
            pass


def _create(c, ip=None):
    h = {**H, **({"X-Forwarded-For": ip} if ip else {})}
    return c.post(
        "/api/sessions",
        headers=h,
        json={"mode": "shield", "scenario": "x", "language": "en", "consent": True},
    )


def test_spoofed_forwarded_for_does_not_bypass_rate_limit(tmp_path):
    with TestClient(make(tmp_path, per_ip_sessions_per_hour=1)) as c:
        assert _create(c, "1.1.1.1").status_code == 200
        assert _create(c, "2.2.2.2").status_code == 429  # new XFF value, same socket peer


def test_forwarded_for_is_read_only_from_trusted_proxies(tmp_path):
    app = make(tmp_path, per_ip_sessions_per_hour=1, trusted_proxies="10.0.0.0/8")
    with TestClient(app, client=("10.0.0.1", 50000)) as c:  # the socket peer is a trusted proxy
        # the rightmost untrusted hop is the real client; entries to its left are only a claim
        assert _create(c, "1.2.3.4, 9.9.9.9").status_code == 200
        assert _create(c, "5.6.7.8, 9.9.9.9").status_code == 429
        assert _create(c, "9.9.9.9, 8.8.8.8, 10.0.0.2").status_code == 200  # a different client
    with TestClient(app, client=("203.0.113.7", 50000)) as c:  # the peer is NOT a trusted proxy
        assert _create(c, "1.1.1.1").status_code == 200
        assert _create(c, "2.2.2.2").status_code == 429  # its header is ignored entirely


def test_budget_exhaustion_serves_labelled_replay_no_blank_screen(tmp_path):
    app = make(tmp_path, demo_mode=True, daily_token_budget=100)
    with TestClient(app) as c:
        app.state.s.budget.forced_exhausted = True
        s = c.post(
            "/api/sessions",
            headers=H,
            json={
                "mode": "honeypot",
                "scenario": "digital-arrest-parcel",
                "language": "en",
                "consent": True,
            },
        ).json()
        assert s["replay"] is True and "replay" in s["notice"].lower()
        assert c.get("/healthz").json()["budget"]["exhausted"] is True
        with c.websocket_connect(f"/ws/sessions/{s['id']}?ticket={s['ws_ticket']}") as ws:
            ev = drain(ws)
        assert ev[0]["type"] == "budget_notice" and ev[0]["replay_source"]
        assert all(e.get("replay") for e in ev) and {"persona_reply", "risk"} <= {
            e["type"] for e in ev
        }
        # Shield analysis stays available (rules-only costs no tokens)
        r = c.post(
            "/api/analyze",
            headers=H,
            json={"text": "You are under digital arrest", "language": "en", "consent": True},
        )
        assert r.status_code == 200
        assert [x["id"] for x in c.get("/api/replays").json()]


def test_explanation_follows_ui_language_not_caller_language(client):
    text = "Main CBI officer hoon. Aap digital arrest mein hain, kisi ko mat batana."
    en = client.post(
        "/api/analyze", headers=H, json={"text": text, "language": "en", "consent": True}
    ).json()
    hi = client.post(
        "/api/analyze", headers=H, json={"text": text, "language": "hi", "consent": True}
    ).json()
    assert en["explanation"]["summary"].isascii()
    assert not hi["explanation"]["summary"].isascii()


def test_report_fields_for_filing_assistant(client):
    text = (
        "This is Inspector Rao from the National Crime Verification Cell. Your Aadhaar is linked to a "
        "case, warrant ready.\nYou are under digital arrest, do not tell anyone.\n"
        "Transfer Rs 90,000 to the RBI safe account simverify@examplebank now."
    )
    a = client.post(
        "/api/analyze", headers=H, json={"text": text, "language": "en", "consent": True}
    ).json()
    r = client.get(f"/api/incidents/{a['incident_id']}/report-fields", headers=H)
    assert r.status_code == 200
    rep = r.json()
    assert rep["never_submits"] is True and rep["portal"] == "https://cybercrime.gov.in"
    groups = {g["group"]: g["fields"] for g in rep["groups"]}
    assert {
        "Complaint type",
        "Incident description",
        "Suspect details",
        "Evidence to upload",
    } <= set(groups)
    suspects = {f["value"] for f in groups["Suspect details"]}
    assert "simverify@examplebank" in suspects
    narrative = groups["Incident description"][0]["value"]
    assert (
        "I have not transferred any money" in narrative
        and "digital arrest" in narrative.lower()
        or "video" in narrative.lower()
    )
    assert (
        client.get(
            f"/api/incidents/{a['incident_id']}/report-fields",
            headers={"X-Client-Id": "client-9999-bbbb"},
        ).status_code
        == 404
    )


def test_incident_feedback_loop(client):
    text = (
        "This is Inspector Rao from the National Crime Verification Cell. Your Aadhaar is linked to a "
        "case, warrant ready.\nYou are under digital arrest, do not tell anyone.\n"
        "Transfer Rs 90,000 to the RBI safe account simverify@examplebank now."
    )
    a = client.post(
        "/api/analyze", headers=H, json={"text": text, "language": "en", "consent": True}
    ).json()
    iid = a["incident_id"]

    # Initially feedback is None
    inc = client.get(f"/api/incidents/{iid}", headers=H).json()
    assert inc["feedback_verdict"] is None

    # Post scam feedback
    fb = client.post(
        f"/api/incidents/{iid}/feedback",
        headers=H,
        json={"verdict": "scam", "notes": "Correct detection of digital arrest"},
    )
    assert fb.status_code == 200
    assert fb.json() == {"id": iid, "verdict": "scam", "saved": True}

    # Verify incident detail shows verdict
    inc = client.get(f"/api/incidents/{iid}", headers=H).json()
    assert inc["feedback_verdict"] == "scam"

    # Verify list of incidents includes feedback_verdict
    incs = client.get("/api/incidents", headers=H).json()
    target = next(i for i in incs if i["id"] == iid)
    assert target["feedback_verdict"] == "scam"

    # Verify feedback stats
    stats = client.get("/api/memory/feedback-stats", headers=H).json()
    assert stats["confirmed_scams"] == 1
    assert stats["false_alarms"] == 0
    assert stats["total_feedback"] == 1
