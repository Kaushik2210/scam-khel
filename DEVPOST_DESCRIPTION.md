# SCAM-KHEL (Devpost description draft)

**Track:** Personal AI · **Built with:** Nebius Token Factory, NVIDIA Nemotron (fast / mid / deep tiers), Tavily, FastAPI, Next.js, SQLite, Telegram Bot API, ReportLab, Python, TypeScript, Tailwind CSS, Playwright

## Inspiration
"Digital arrest" scams drain savings from people who are told, on a video call, that police or the CBI are about to arrest them or a family member. The caller isolates the victim ("tell no one") and demands a transfer to a "safe account". Older relatives are the usual targets, and families usually find out after the money is gone. Authorities say police, CBI, ED and courts do not arrest anyone over a video call; victims should call 1930 and report at cybercrime.gov.in.

## What it does
SCAM-KHEL is a private family shield with four parts:
1. **Shield:** paste, speak or stream what a caller said. A hybrid detector (deterministic English/Hindi/Hinglish rules + a Nemotron tagger) names the coercion tactics, scores risk 0-100 and explains in plain language what to do now.
2. **Honeypot (simulation):** a decoy "confused grandmother" persona stalls a built-in simulated scammer, eliciting names, badge IDs, phone numbers, UPI IDs and accounts while a counter shows the time wasted. It uses only fictional decoy data and never pays, installs or clicks.
3. **Personal memory:** scripts are fingerprinted and remembered; a repeat is recognised earlier ("flagged at turn 2 vs turn 4 earlier") and treated as high risk immediately.
4. **Real actions:** a Telegram alert to the family, a complaint draft (PDF/Markdown, never auto-filed) for cybercrime.gov.in, a blocklist export, and an "I already sent money" panic flow with a 1930 call script.

## How we built it
All runtime LLM calls go to **Nebius Token Factory**, using three **NVIDIA Nemotron** tiers by cost: the *fast* tier tags every message and screens for prompt injection, the *mid* tier plays the persona and the simulator, the *deep* tier writes the final analysis. Tavily verifies claims against official advisories and searches for public reports at run time. A privacy layer masks personal numbers before any model call, encrypts transcripts at rest, and enforces a consent screen and 30-day retention. An output guard blocks any persona reply that resembles real personal data or agrees to a payment.

## Challenges
Keeping a security tool honest: negation ("never share your OTP") must not look like a scam; a public scam-awareness advisory must not trigger alarms (we found this on a held-out set and report the fix transparently); the persona must resist an adversarial scammer that tries prompt injection; and a free public demo needs a token budget with a graceful replay mode instead of a blank screen.

## Accomplishments
Measured eval on 43 labelled dialogues (see README), a safety suite with zero persona leakage across 250+ hostile cases, a reproducible memory benefit, and a full browser end-to-end smoke test.

## What we learned
Cheap deterministic rules plus a small model for recall, and an expensive model only once per incident, keeps cost predictable. See `DEVLOG.md` for tool friction.

## What's next
Real bait-line telephony behind a consent-gated feature flag, on-device ASR, more regional languages, bank and telecom blocklist integrations, embeddings-based script retrieval.

**Honest limits:** simulation only; drafts not filings; detection can be wrong; live Token Factory / Tavily / Telegram paths were unit-tested with mocks (see `docs/FINAL_AUDIT.md`).
