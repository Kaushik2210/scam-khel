"""The example-env guard and the gitleaks config that backs it."""

import importlib.util
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_env_example.py"

spec = importlib.util.spec_from_file_location("check_env_example", SCRIPT)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

# Not real credentials; shaped like them so the tests exercise realistic values.
FAKE = "tvly-dev-0123456789abcdefFAKEFAKEFAKE"


def flagged(text: str) -> list[tuple[int, str]]:
    return list(guard.findings(text))


@pytest.mark.parametrize(
    "line",
    [
        "TAVILY_API_KEY=",
        "TELEGRAM_BOT_TOKEN=   # create via @BotFather",
        'FERNET_KEY=""',
        "ADMIN_TOKEN=''",
        "# NEBIUS_API_KEY=" + FAKE,
        "",
        "   ",
        "JUST TEXT",
    ],
)
def test_blank_commented_and_non_assignment_lines_pass(line):
    assert flagged(line) == []


@pytest.mark.parametrize(
    "line,name",
    [
        (f"TAVILY_API_KEY={FAKE}", "TAVILY_API_KEY"),
        (f"TELEGRAM_BOT_TOKEN = {FAKE}", "TELEGRAM_BOT_TOKEN"),
        (f'NEBIUS_API_KEY="{FAKE}"', "NEBIUS_API_KEY"),
        (f"FERNET_KEY='{FAKE}'", "FERNET_KEY"),
        (f"export ADMIN_TOKEN={FAKE}", "ADMIN_TOKEN"),
        (f"DB_PASSWORD={FAKE}  # prod", "DB_PASSWORD"),
        (f"webhook_secret={FAKE}", "webhook_secret"),
        (f"STRIPE_SECRET={FAKE}", "STRIPE_SECRET"),
    ],
)
def test_a_value_on_a_secret_named_variable_is_flagged(line, name):
    assert flagged(f"A=1\n{line}\n") == [(2, name)]


@pytest.mark.parametrize(
    "line",
    [
        "DAILY_TOKEN_BUDGET=500000",  # contains TOKEN but is a number, not a credential
        "NEXT_PUBLIC_API_URL=http://localhost:8000",
        "FRONTEND_ORIGIN=http://localhost:3000",
        "STRUCTURED_MODE=json_prompt",
        "MAX_TURNS_PER_SESSION=20",
    ],
)
def test_ordinary_settings_are_not_flagged(line):
    assert flagged(line) == []


def test_the_repository_example_files_are_clean():
    files = guard.tracked_example_files()
    assert ".env.example" in files and "frontend/.env.example" in files
    for path in files:
        text = (ROOT / path).read_text(encoding="utf-8")
        assert flagged(text) == [], path


def test_cli_exits_nonzero_and_never_prints_the_value(tmp_path):
    leaked = tmp_path / ".env.example"
    leaked.write_text(f"OK=1\nTAVILY_API_KEY={FAKE}\n", encoding="utf-8")
    run = subprocess.run(
        [sys.executable, str(SCRIPT), str(leaked)], capture_output=True, text=True, cwd=ROOT
    )
    assert run.returncode == 1
    assert "TAVILY_API_KEY has a value" in run.stdout and f"{leaked}:2" in run.stdout
    assert FAKE not in run.stdout + run.stderr and "0123456789" not in run.stdout + run.stderr

    clean = tmp_path / "clean.env.example"
    clean.write_text("TAVILY_API_KEY=\n", encoding="utf-8")
    ok = subprocess.run(
        [sys.executable, str(SCRIPT), str(clean)], capture_output=True, text=True, cwd=ROOT
    )
    assert ok.returncode == 0 and ok.stdout == ""


def test_the_historic_leak_commit_would_have_been_caught():
    """Replays the real commit that added all three values (names only, values never printed)."""
    try:
        history = subprocess.run(
            ["git", "show", "6ff9ea1a4307f3576909fab756fc8643a5c3dbc8:.env.example"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("full git history is not available (shallow checkout)")
    assert [name for _, name in flagged(history)] == [
        "TAVILY_API_KEY",
        "TELEGRAM_BOT_TOKEN",
        "FERNET_KEY",
    ]


@pytest.fixture(scope="module")
def gitleaks():
    return tomllib.loads((ROOT / ".gitleaks.toml").read_text(encoding="utf-8"))


def test_gitleaks_config_extends_the_defaults_and_has_the_custom_rules(gitleaks):
    assert gitleaks["extend"]["useDefault"] is True
    assert {r["id"] for r in gitleaks["rules"]} == {"fernet-key", "secret-value-in-example-env"}


def test_gitleaks_allowlist_only_names_the_three_known_commits(gitleaks):
    commits = gitleaks["allowlist"]["commits"]
    assert commits == [
        "9ee6c4dcc4170f4f2ef119b04c7399066f983d7d",
        "1d49a81e46c4158b91844755b69e9c10f0e2c767",
        "6ff9ea1a4307f3576909fab756fc8643a5c3dbc8",
    ]
    assert all(re.fullmatch(r"[0-9a-f]{40}", c) for c in commits)
    assert "paths" not in gitleaks["allowlist"] and "regexes" not in gitleaks["allowlist"]


def test_gitleaks_custom_rule_regexes_match_leaks_and_spare_settings(gitleaks):
    """Approximated with Python's re (gitleaks uses Go's RE2; these patterns avoid the differences)."""
    rules = {r["id"]: r for r in gitleaks["rules"]}

    fernet = re.compile(rules["fernet-key"]["regex"])
    assert fernet.search("FERNET_KEY=" + "A" * 43 + "=")
    assert fernet.search('fernet-key: "' + "a_-" * 14 + 'a="')  # 43 characters then '='
    assert not fernet.search("FERNET_KEY=")

    env = rules["secret-value-in-example-env"]
    path, rx = re.compile(env["path"]), re.compile(env["regex"])
    assert path.search(".env.example") and path.search("frontend/.env.example")
    assert not path.search("backend/app/config.py") and not path.search(".env")
    assert rx.search(f"TAVILY_API_KEY={FAKE}\n")
    assert rx.search(f'TELEGRAM_BOT_TOKEN = "{FAKE}"')
    assert not rx.search("TAVILY_API_KEY=\n")
    assert not rx.search("ADMIN_TOKEN=   # leave empty\n")
    assert not rx.search("DAILY_TOKEN_BUDGET=500000\n")
