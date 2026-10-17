# Privacy

SCAM-KHEL is designed local-first and minimal. This page describes what the code actually does (DPDP-style: purpose, minimisation, retention, rights).

**Purpose.** Detect scam tactics in text you provide, alert your chosen family contacts, and prepare a complaint *draft*.

**Consent.** Before any analysis a consent sheet states purpose, what is stored, retention and how to delete. A consent record (notice version, purposes, timestamp) is stored server-side. Without consent the API refuses to analyse.

**What is stored.** Transcripts (Fernet-encrypted at rest), extracted identifiers of the *caller* (phone numbers, UPI IDs...), tactic timelines, family circle labels and Telegram chat IDs you link, consent and alert logs. **No audio is stored**; the browser transcribes speech locally and only text is sent.

**What leaves the server.** Text sent to Nebius Token Factory (NVIDIA Nemotron) is first sanitised: Aadhaar, PAN, card, OTP, phone, UPI, IFSC and account patterns are masked, and family names are replaced with `FAMILY_n`. Phone/UPI-type identifiers are extracted by local regex and are not sent to an LLM. Tavily receives only search queries built from claimed agency names and caller identifiers. Telegram receives alert text (risk level, tactic summary, link).

**Retention.** `RETENTION_DAYS` (default 30). `scripts/purge.py` deletes older sessions and dependants; run it from cron.

**Your rights.** `DELETE /api/me/data` (and the "Delete all my data" button) removes your sessions, transcripts, evidence, incidents, alerts, family circle and consent records, plus any learned scam script derived only from your incidents.

**Logs.** Structured logs redact Aadhaar/PAN/phone/card/token patterns; every line carries a request ID.

**Third parties.** No trackers, ads or analytics. Processors: Nebius (LLM), Tavily (search), Telegram (alerts), your hosting provider.

**Limits.** This is a hackathon prototype, not a certified compliance product. Review before processing real people's data.
