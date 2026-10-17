import csv
import io
import json

import pytest

from app.actions.blocklist import to_csv, to_json
from app.actions.complaint import DRAFT_BANNER, build_markdown
from app.actions.pdf import render_pdf
from app.orchestrator import Orchestrator
from app.verify.tavily_verifier import NO_REPORTS_NOTE, OFFICIAL_DOMAINS, TavilyVerifier


class FakeTavily:
    def __init__(self, results=None, exc=None):
        self.calls = []
        self.results = (
            results
            if results is not None
            else [
                {
                    "title": "Advisory",
                    "url": "https://pib.gov.in/x",
                    "content": "No arrests on video call",
                }
            ]
        )
        self.exc = exc

    async def search(self, query, **kw):
        self.calls.append((query, kw))
        if self.exc:
            raise self.exc
        return {"results": self.results}


async def test_advisory_uses_official_domains_and_caches():
    f = FakeTavily()
    v = TavilyVerifier(client=f)
    a = await v.fetch_advisory()
    b = await v.fetch_advisory()
    assert a.status == "ok" and not a.cached and b.cached
    assert len(f.calls) == 1
    assert f.calls[0][1]["include_domains"] == OFFICIAL_DOMAINS
    assert a.sources[0].url.startswith("https://pib.gov.in")


async def test_report_search_not_domain_restricted_and_no_results_is_not_safe():
    f = FakeTavily(results=[])
    v = await TavilyVerifier(client=f).search_reports("simverify@examplebank")
    assert f.calls[0][1]["include_domains"] is None
    assert v.status == "no_results" and v.note == NO_REPORTS_NOTE
    assert "NOT mean it is safe" in NO_REPORTS_NOTE


@pytest.mark.parametrize("exc", [RuntimeError("quota"), TimeoutError()])
async def test_quota_and_errors_degrade_gracefully(exc):
    v = await TavilyVerifier(client=FakeTavily(exc=exc)).check_claim("Some Cell")
    assert v.status == "unavailable" and "not a safety signal" in v.note


async def test_no_key_and_call_budget():
    assert (await TavilyVerifier().fetch_advisory()).status == "unavailable"
    tv = TavilyVerifier(client=FakeTavily(), max_calls=1)
    await tv.check_claim("a")
    assert (await tv.check_claim("b")).note == "Verification budget reached."


async def run_session(verifier=None):
    return await Orchestrator(seed=1, verifier=verifier).run(
        "digital-arrest-parcel", "honeypot", max_turns=8
    )


async def test_orchestrator_emits_verification_events():
    events = []

    async def emit(t, p):
        if t == "verification":
            events.append(p)

    f = FakeTavily()
    sm = await Orchestrator(seed=1, emit=emit, verifier=TavilyVerifier(client=f)).run(
        "digital-arrest-parcel", "honeypot", 8
    )
    kinds = [e["kind"] for e in events]
    assert "advisory" in kinds and "report_search" in kinds and "claim_check" in kinds
    assert len(sm.verifications) == len(events) <= 6
    assert all(e["provider"] == "tavily" for e in events)


async def test_blocklist_csv_json_and_formula_injection():
    ev = [
        {"type": "phone", "value": "+919000000481", "confidence": 0.9, "mentions": 2},
        {"type": "phone", "value": "+919000000481"},
        {"type": "upi", "value": "=cmd|' /C calc'!A0", "confidence": 0.7},
        {"type": "agency", "value": "X Cell"},
    ]
    rows = list(csv.DictReader(io.StringIO(to_csv(ev))))
    assert len(rows) == 2 and rows[1]["value"].startswith("'=")
    j = json.loads(to_json(ev, simulation=True))
    assert j["simulation"] and len(j["items"]) == 2


async def test_complaint_markdown_and_pdf_from_session():
    sm = await run_session(TavilyVerifier(client=FakeTavily()))
    d = sm.complaint_data({"Amount": "Rs 1,000", "Date": "2026-10-17"})
    md = build_markdown(d)
    assert DRAFT_BANNER in md and "1930" in md and "cybercrime.gov.in" in md
    assert "SIMULATION" in md and "Complainant (fill in)" in md
    assert "Transaction details" in md and "simverify@examplebank" in md
    assert len({e["type"] for e in sm.evidence}) >= 5

    pdf = render_pdf(d)
    assert pdf[:5] == b"%PDF-" and len(pdf) > 3000
    from pypdf import PdfReader  # type: ignore[import-not-found]

    text = "".join(p.extract_text() for p in PdfReader(io.BytesIO(pdf)).pages)
    assert "DRAFT" in text and "1930" in text and "simverify@examplebank" in text


def test_complaint_redacts_personal_data_by_default():
    from app.actions.complaint import ComplaintData

    d = ComplaintData(
        None,
        "x",
        False,
        80,
        "s",
        transcript=[{"turn": 1, "speaker": "victim", "text": "OTP is 482913 call 9999900000"}],
    )
    assert "482913" not in build_markdown(d) and "9999900000" not in build_markdown(d)
    assert "482913" in build_markdown(d, redact=False)
