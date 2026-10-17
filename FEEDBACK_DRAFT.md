# Hackathon feedback form: draft

> Pre-filled from `DEVLOG.md`. Items marked **[YOU: ...]** need your real experience with the live services; I had no API keys while building, so I will not invent how they behaved.

## What I used each tool for
- **Nebius Token Factory:** the only runtime LLM provider, through its OpenAI-compatible API (`openai` Python SDK with `base_url`). Three tiers for tagging, persona/simulation and final analysis. A `check_models.py` script lists models, smoke-tests each tier and probes tool-calling / JSON support.
- **NVIDIA Nemotron:** fast / mid / deep model tiers selected by env var. **[YOU: which exact model IDs you chose for each tier and why.]**
- **Tavily:** runtime verification: official-advisory fetch restricted to government domains, claim check, best-effort report search, with caching and quota-error handling.
- (Also: Telegram Bot API for family alerts; no other LLM or search providers.)

## What worked
- OpenAI-compatible API meant zero custom client code; retries/streaming/usage accounting were straightforward. **[YOU: onboarding time from signup to first successful call: ___ min; latency/throughput you saw per tier; whether JSON mode / tool calling worked reliably.]**
- Tavily's `include_domains` made the "official sources only" requirement a one-line parameter (verified against the installed client's signature, not against live results).

## What needs work / friction (from DEVLOG)
- The Token Factory docs show more than one base URL host; I left `NEBIUS_BASE_URL` configurable and flagged it for verification. **[YOU: which host actually worked.]**
- Model IDs and reasoning on/off switches can't be assumed; `<think>` blocks are stripped client-side as a precaution. **[YOU: whether your chosen Nemotron models emit reasoning and how you turned it off.]**
- Recent `openai` SDK versions use `httpx2` internally, so common HTTP mocking tools (respx) don't intercept it; tests inject an `httpx2.MockTransport` instead. Worth a docs note for people building OpenAI-compatible clients.
- Tavily's client signature is large and changes between versions; I pinned behaviour with tests against a fake client. **[YOU: quota/rate-limit behaviour you hit on the free tier.]**

## Would I build with these again?
**[YOU: yes/no and why, naming the tool each time.]** Draft answer if true for you: yes for Token Factory (OpenAI compatibility + tiered Nemotron models made cost tiering easy to demonstrate) and for Tavily (domain-restricted search directly supported the trust story).

## Suggestions
- A documented list of recommended Nemotron models per use case (tagger / chat / long-form), with latency and price, in the Token Factory console.
- A sandbox key that is explicitly rate-limited rather than silently failing, so demo builders can design budget protection.
