#!/usr/bin/env python3
"""Fail if an example env file gives a secret-named variable a value.

`.env.example` is committed and public. It documents which variables exist; real values belong
in `.env`, which is git-ignored. Variables whose name ends in _KEY, _TOKEN, _SECRET or _PASSWORD
must therefore stay empty here.

Usage: check_env_example.py [FILE ...]   (no files: every tracked .env*.example file)
Prints variable names and line numbers, never values, so a failing run does not leak the secret
into CI logs a second time. Standard library only.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

SECRET_NAME = re.compile(
    r"^[A-Za-z][A-Za-z0-9_]*_(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD)$", re.IGNORECASE
)
EXAMPLE_FILE = re.compile(r"(^|/)\.env[^/]*\.example$")
ROOT = Path(__file__).resolve().parent.parent


def _value(raw: str) -> str:
    """The assigned value without quotes or a trailing ` # comment`."""
    raw = raw.strip()
    if raw[:1] in ("'", '"'):
        end = raw.find(raw[0], 1)
        return raw[1:end] if end != -1 else raw[1:]
    return re.split(r"(?:^|\s)#", raw, maxsplit=1)[0].strip()


def findings(text: str) -> Iterator[tuple[int, str]]:
    """Yield (line number, variable name) for each secret-named variable that has a value."""
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, _, raw = stripped.removeprefix("export ").partition("=")
        name = name.strip()
        if SECRET_NAME.match(name) and _value(raw):
            yield number, name


def tracked_example_files() -> list[str]:
    """Tracked example env files, as paths relative to the repository root."""
    git = shutil.which("git") or "git"
    out = subprocess.run(  # noqa: S603 - fixed argument list, no caller input
        [git, "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    return [p for p in out.splitlines() if EXAMPLE_FILE.search(p)]


def main(argv: list[str]) -> int:
    targets = [(p, Path(p)) for p in argv] or [(p, ROOT / p) for p in tracked_example_files()]
    bad = 0
    for path, location in targets:
        for number, name in findings(location.read_text(encoding="utf-8", errors="replace")):
            bad += 1
            print(f"{path}:{number}: {name} has a value (not shown)")
    if bad:
        print(
            "\nExample env files must leave secret-named variables empty. Put real values in .env "
            "(git-ignored).\nIf a real credential was committed, treat it as compromised: revoke "
            "and rotate it first.\nBlanking it in a later commit does not remove it from git history."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
