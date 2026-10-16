"""Validate Token Factory models, probe capabilities, write docs/model_report.md.

Usage: python scripts/check_models.py   (run from backend/)
"""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from app.config import Tier, get_settings
from app.llm.client import LLMClient, LLMError, StructuredOutputError

REPORT = Path(__file__).resolve().parents[2] / "docs" / "model_report.md"
TIERS: list[Tier] = ["fast", "mid", "deep"]


class Probe(BaseModel):
    ok: bool
    word: str


TOOL = {
    "type": "function",
    "function": {
        "name": "report",
        "description": "Report result",
        "parameters": {
            "type": "object",
            "properties": {"ok": {"type": "boolean"}, "word": {"type": "string"}},
            "required": ["ok", "word"],
        },
    },
}


async def probe_tools(client: LLMClient, tier: Tier) -> bool:
    try:
        resp = await client.client.chat.completions.create(
            model=client.s.model_for(tier),
            messages=[{"role": "user", "content": "Call report with ok=true, word='hi'."}],
            tools=[TOOL],  # type: ignore[list-item]
            tool_choice={"type": "function", "function": {"name": "report"}},
            max_tokens=200,
        )
        calls = resp.choices[0].message.tool_calls
        return bool(calls and "ok" in calls[0].function.arguments)  # type: ignore[union-attr]
    except Exception:  # capability probe
        return False


async def main() -> int:
    s = get_settings()
    lines = [
        "# Model report",
        f"\nGenerated {datetime.now(UTC).isoformat(timespec='seconds')}"
        f" against `{s.nebius_base_url}`\n",
    ]
    if not s.nebius_api_key:
        msg = "NEBIUS_API_KEY not set. See docs/MANUAL_STEPS.md (create key, claim credits)."
        print(msg, file=sys.stderr)
        REPORT.write_text("\n".join([*lines, f"**NOT RUN:** {msg}\n"]), encoding="utf-8")
        return 2
    client = LLMClient(s)
    try:
        available = await client.list_models()
    except Exception as e:
        print(f"GET /models failed: {e!r}", file=sys.stderr)
        return 2
    nv = [m for m in available if "nemotron" in m.lower() or "nvidia" in m.lower()]
    print("NVIDIA models:\n  " + "\n  ".join(nv or ["(none found)"]))
    lines += ["## NVIDIA models available", *[f"- `{m}`" for m in nv], ""]
    lines += [
        "## Tier validation",
        "| tier | model | exists | smoke | latency ms | json (prompt) | tools |",
        "|---|---|---|---|---|---|---|",
    ]

    failed = False
    tools_ok_all = True
    json_ok_all = True
    for tier in TIERS:
        model = s.model_for(tier)
        exists = model in available
        smoke = jsn = tools = False
        lat = float("nan")
        if exists:
            try:
                r = await client.chat(tier, [{"role": "user", "content": "Say OK"}], max_tokens=8)
                smoke, lat = bool(r.text) or True, r.latency_ms
            except LLMError as e:
                print(f"{tier} smoke failed: {e}", file=sys.stderr)
            try:
                await client.structured(
                    tier, [{"role": "user", "content": "ok=true, word='hi'"}], Probe
                )
                jsn = True
            except (StructuredOutputError, LLMError):
                jsn = False
            tools = await probe_tools(client, tier)
        failed |= not (exists and smoke)
        tools_ok_all &= tools
        json_ok_all &= jsn
        lines.append(
            f"| {tier} | `{model or '(unset)'}` | {exists} | {smoke} | {lat:.0f} "
            f"| {jsn} | {tools} |"
        )

    rec = "tools" if tools_ok_all else "json_prompt"
    lines += [
        "",
        f"**Recommended `STRUCTURED_MODE`: `{rec}`**"
        + ("" if json_ok_all else " (warning: JSON-prompt protocol failed on some tier)"),
        "",
        "Embeddings: not probed; FTS5 + tactic-sequence similarity is used for retrieval.",
    ]
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {REPORT}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
