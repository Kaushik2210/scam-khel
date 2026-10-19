# Contributing

Thanks for helping protect families from digital-arrest scams. Please read the [Code of Conduct](CODE_OF_CONDUCT.md) first.

## Ground rules

1. **Synthetic data only.** No real phone numbers, UPI IDs, Aadhaar/PAN, call recordings or victim stories in code, fixtures, issues or PRs. Fictional identifiers use `90000 00xxx` phones and `...@examplebank` UPI IDs.
2. **Simulation stays labelled.** Fictional agencies must contain `(SIMULATION)`; the scenario loader enforces it. Never add code that contacts real scammers or real numbers.
3. **No real agency logos or trademarks** in the UI or assets.
4. **Safety changes need tests.** Anything touching the persona, output guard, sanitizer or injection filter needs a case in the safety suite. The persona leakage rate must stay 0.
5. **Do not tune to the eval.** Add new dialogues to `backend/evals/datasets/dialogues_eval.yaml`. If you change rules after seeing a failure, say so in the PR.

## Setup

```bash
git clone https://github.com/Kaushik2210/scam-khel && cd scam-khel
cp .env.example .env          # keys are optional: offline mode works without any
make setup
cd frontend && npm install
```

## Secrets

This repository is public, and git history is forever.

- Real keys and tokens go in `.env`, which is git-ignored. **Never** in `.env.example`, a test, a doc or a commit message: the example files list which variables exist and must leave every `*_KEY`, `*_TOKEN`, `*_SECRET` and `*_PASSWORD` empty.
- Install the hooks once: `pip install pre-commit && pre-commit install`. They run gitleaks on what you stage and `scripts/check_env_example.py` on example env files.
- CI repeats both checks and also scans the **whole** history on every push, because a secret that is committed and then removed in the next commit is still public.
- **If you committed a real credential, assume it is compromised.** Revoke or rotate it at the provider first (Tavily, BotFather `/revoke`, a new `FERNET_KEY`, ...), then fix the file. Deleting the line in a follow-up commit, or force-pushing, does not make it private again, because clones and caches already have it. Tell a maintainer so the key owner can confirm the rotation.
- Do not add commits to the allowlist in `.gitleaks.toml` to get a build green. Rotate the credential instead; the allowlist only records findings that were already public and handled.
- Maintainers: enable GitHub secret scanning with push protection and branch protection on `main` (require the `secret scan` check). A failed check on a direct push does not block anything by itself.

## Everyday commands

| Command | What it does |
|---|---|
| `make dev` / `cd frontend && npm run dev` | API on :8000 / UI on :3000 |
| `make test` | Backend tests (live tests skip without a key) |
| `make lint` | ruff + mypy (strict) |
| `make eval` | Offline eval; refreshes `backend/evals/report.md` and the README table |
| `make e2e` | Playwright (set `PW_CHANNEL=msedge` or `chrome` if the bundled Chromium cannot launch) |
| `make demo` | Reset and seed demo data |

Frontend: `npm run lint && npm run typecheck && npm run build`.

## Style

- Python: ruff (format and lint), mypy strict, type hints, small modules.
- TypeScript: strict mode, no `any` without a reason.
- UI follows Apple HIG principles translated to the web: semantic colours, 44px targets, visible focus, reduced motion, light and dark, EN/HI strings in `lib/i18n.tsx`.
- Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`). Keep PRs focused and fill in the template.

## Releasing

Update `CHANGELOG.md`, bump versions, tag `vX.Y.Z`.
