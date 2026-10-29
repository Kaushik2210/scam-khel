# Eval report

Generated 2026-10-29T03:47:47+00:00 · mode: **live (Nebius Token Factory + Nemotron)**

| Metric | Result |
|---|---|
| Eval set | 43 dialogues (26 scam / 17 legit; EN, Hindi, Hinglish) |
| Precision / recall / F1 @ high (≥70), all | 0.929 / 1.0 / 0.963 |
| Same, held-out set only (21) | 1.0 / 1.0 / 1.0 |
| False-positive rate on legit (all / held-out) | 0.118 / 0.0 |
| Mean scammer turns to reach high | 2.15 |
| Critical by first payment demand | 1.0 |
| Honeypot engaged turns / time wasted (mean, 7 scenarios) | 10.1 / 805s |
| Identifier types extracted per session (mean) | 8.3 |
| Persona leakage rate (guard violations per persona turn) | 0.0000 |
| Memory benefit: turns saved on 2nd exposure (mean) | 1.43 |
| Run mode | live (Nebius Token Factory + Nemotron) |

> The *tuned* set (dialogues_p1.yaml) was used while writing the rules, so its numbers are optimistic. The *held-out* set was written afterwards; trust that one more.
>
> Disclosure: on its first run the held-out set had one false positive (a public scam-awareness advisory; held-out F1 0.917, FP rate 0.111). An awareness-context dampener was added afterwards, so the held-out numbers here are post-fix and no longer purely held-out. The late scams listed below were left as known limitations: the rules-only detector is weakest on paraphrase (the Nemotron tagger is meant to cover that; run `make eval-live` to measure it).

## Detection by set
| set | n | P | R | F1 | FP rate |
|---|---|---|---|---|---|
| tuned | 22 | 0.875 | 1.0 | 0.933 | 0.25 |
| held-out | 21 | 1.0 | 1.0 | 1.0 | 0.0 |

## By language
| language | n | P | R | F1 |
|---|---|---|---|---|
| en | 24 | 0.929 | 1.0 | 0.963 |
| hi | 5 | 1.0 | 1.0 | 1.0 |
| hinglish | 14 | 0.9 | 1.0 | 0.947 |

## Misclassified / late dialogues

- `legit-04-emi-reminder` (legit, peak 74, critical_by_payment=None)
- `legit-05-family-chat-hinglish` (legit, peak 85, critical_by_payment=None)

## Honeypot
| scenario | engaged | wasted | id types | ids | leaks | rewrites | injections |
|---|---|---|---|---|---|---|---|
| adversarial-injection | 10 | 777s | 6 | 6 | 0 | 2 | 0 |
| courier-drug-package | 11 | 945s | 9 | 15 | 0 | 1 | 0 |
| digital-arrest-money-laundering | 12 | 947s | 10 | 23 | 0 | 2 | 0 |
| digital-arrest-parcel | 12 | 918s | 8 | 18 | 0 | 0 | 0 |
| fake-customs | 9 | 575s | 9 | 14 | 0 | 0 | 0 |
| fake-police-family-accident | 9 | 710s | 10 | 13 | 0 | 0 | 0 |
| kyc-expiry-bank | 8 | 764s | 6 | 9 | 0 | 0 | 0 |

## Memory benefit (turn at which risk first ≥ high)
| scenario | 1st exposure | 2nd exposure | memory-hit turn |
|---|---|---|---|
| adversarial-injection | 1 | 1 | None |
| courier-drug-package | 2 | 1 | 1 |
| digital-arrest-money-laundering | 4 | 2 | None |
| digital-arrest-parcel | 2 | 1 | 1 |
| fake-customs | 3 | 2 | None |
| fake-police-family-accident | 2 | 1 | 1 |
| kyc-expiry-bank | 5 | 1 | None |

## Latency and tokens per tier

Live run: 734861 tokens over ~64 analysed units.

| tier | calls | prompt tok | completion tok | p50 ms | p95 ms |
|---|---|---|---|---|---|
| fast | 293 | 203356 | 37217 | 2263.7 | 5093.3 |
| mid | 552 | 400987 | 40914 | 1302.1 | 4611.2 |
| deep | 20 | 40218 | 12169 | 20358.0 | 59577.6 |
