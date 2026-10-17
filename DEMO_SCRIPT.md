# Demo script (3:00)

**Rules:** no third-party logos/trademarks, no copyrighted music (use silence or CC0 audio). Every simulator screen visibly says SIMULATION. Say "simulation", never "catches criminals".

## Reset / seed (run before recording)
```bash
make demo                              # resets DB, seeds 2 prior incidents (digital-arrest-parcel, kyc-expiry-bank)
make dev                               # API :8000   | in another terminal: cd frontend && npm run dev
# open once:  http://localhost:3000/?client=demo-client-0001   (tick the consent sheet once)
# optional, real services: set TELEGRAM_BOT_TOKEN and link your phone via /family; set TAVILY_API_KEY; set NEBIUS_API_KEY + MODEL_*
```
Browser: 1440x900, dark mode, zoom 110%, English UI (switch to Hindi at 2:35 for 3 seconds).

## Timeline

| Time | Screen state | Narration | Action |
|---|---|---|---|
| 0:00-0:20 | Landing page, then a still of the Parent view | "Every week, Indians lose savings to fake-police video calls: 'digital arrest'. The caller says you are implicated, keeps you on camera, and demands a transfer to a safe account. Real police never arrest anyone over a video call. SCAM-KHEL is a private shield for the family." | Scroll the three-step explainer slowly |
| 0:20-0:50 | `/live` (Shield). Paste: *"This is Inspector Rao (SIMULATION). Your Aadhaar is linked to money laundering, a warrant is ready. You are under digital arrest, stay on the video call and do not tell anyone. Transfer Rs 90,000 to the RBI safe account now."* | "Paste what the caller said. Within one message the risk meter goes to critical, the tactics are named in plain language, and it tells you what to do: hang up, don't pay, call 1930." | Click Check now; hold on the meter and the "what to do" list |
| 0:50-1:40 | `/simulate`, scenario *Digital arrest - parcel*, autoplay speed 2x | "Now the honeypot. A simulated scammer, fictional agency, versus a decoy grandmother. She never pays, never installs, never shares a code; she stalls and asks for his name, badge and account. Watch the evidence panel fill: phone, UPI, account, IFSC, badge, case. The counter shows the scammer's time wasted." | Start; point at the SIMULATION badge, evidence panel, time-wasted counter |
| 1:40-2:10 | Same screen, Tavily panel; then run **KYC expiry** (already seeded, so this is its second exposure) | "Tavily checks official advisories and public reports at run time. And it remembers: this second run of a script it has seen is recognised at turn 2 instead of turn 4, with the incident it learned from." | Show verification sources; point at the memory banner |
| 2:10-2:40 | Phone showing Telegram alert; click *Complaint draft (PDF)*; open PDF; then `/parent` red button | "The family gets a Telegram alert. A complaint draft for cybercrime.gov.in is ready to review; it never files anything. And for someone who already sent money: one red button, a 1930 checklist, a script to read, and the form pre-filled." | Download PDF, scroll the DRAFT banner; press panic, fill amount, show script. Flip to Hindi for 3 s |
| 2:40-3:00 | `/about` architecture + tier table | "Everything runs on Nebius Token Factory with NVIDIA Nemotron: a fast tier tags every message, a mid tier plays the persona, a deep tier writes the final analysis. Built with Tavily, FastAPI and Next.js. Nebius Token Factory. NVIDIA Nemotron." | On-screen text: *Nebius Token Factory · NVIDIA Nemotron · Tavily* |

## Shot list
1. Landing (title, 3 steps). 2. Consent sheet (brief). 3. Shield result at critical. 4. Simulation split view (wide). 5. Close-up: evidence panel. 6. Close-up: memory banner. 7. Tavily sources. 8. Telegram alert on phone. 9. PDF first page. 10. Parent panic flow. 11. About page tier table + end card.

## Required screen states
- Risk meter at **critical** with the "what to do now" list visible.
- Evidence panel with at least 6 identifiers (phone, UPI, account, IFSC, badge/case, agency).
- Memory banner: "Recognised pattern from Incident #N, flagged at turn k vs turn m earlier".
- Tavily panel showing at least one source link (needs `TAVILY_API_KEY`; otherwise it honestly shows "unavailable").
- Telegram alert delivered (needs a bot token and a linked chat).
- PDF showing the DRAFT banner and the 1930 / cybercrime.gov.in line.

## Rehearsal notes
The offline path (no keys) was rehearsed by the Playwright smoke test (landing -> consent -> simulation -> critical -> evidence -> PDF; second-exposure memory banner; parent/panic/Hindi; Shield + delete-all). The live-key, Telegram and Tavily segments have **not** been rehearsed against real services: do one full dry run with real keys before recording and time it to <= 3:00.
