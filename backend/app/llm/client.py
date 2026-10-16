"""Async Nebius Token Factory client (OpenAI-compatible) with tier routing.

Only talks to Nebius Token Factory. The `openai` SDK is used purely as an HTTP transport.
"""

from __future__ import annotations

import asyncio
import json
import random
import re
import time
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import Any, TypeVar

import openai
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from app.config import Settings, Tier, get_settings
from app.llm.usage import UsageRecord, UsageTracker
from app.llm.usage import tracker as default_tracker
from app.logging import get_logger, request_id_var

log = get_logger("llm")
T = TypeVar("T", bound=BaseModel)

_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_THINK_OPEN = re.compile(r"^.*?</think>", re.DOTALL | re.IGNORECASE)  # dangling close tag
_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)

RETRYABLE = (
    openai.RateLimitError,
    openai.APIConnectionError,
    openai.APITimeoutError,
    openai.InternalServerError,
)


class LLMError(RuntimeError):
    pass


class StructuredOutputError(LLMError):
    pass


def strip_think(text: str) -> str:
    """Remove reasoning blocks (<think>…</think>), including a lone closing tag."""
    text = _THINK_BLOCK.sub("", text)
    if "</think>" in text.lower():
        text = _THINK_OPEN.sub("", text)
    return text.strip()


def extract_json(text: str) -> Any:
    """Parse the first JSON object/array found in model output (after think-strip/fences)."""
    text = _FENCE.sub("", strip_think(text).strip())
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    dec = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch in "{[":
            try:
                obj, _ = dec.raw_decode(text[i:])
                return obj
            except json.JSONDecodeError:
                continue
    raise StructuredOutputError("no JSON found in model output")


@dataclass
class ChatResult:
    text: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    model: str


OfflineHandler = Callable[[Tier, list[dict[str, str]]], str]


class LLMClient:
    def __init__(
        self,
        settings: Settings | None = None,
        tracker: UsageTracker | None = None,
        offline_handler: OfflineHandler | None = None,
        sleep: Callable[[float], Any] = asyncio.sleep,
        http_client: Any = None,
    ) -> None:
        self._http_client = http_client
        self.s = settings or get_settings()
        self.tracker = tracker or default_tracker
        self.offline_handler = offline_handler
        self._sleep = sleep
        self._client: AsyncOpenAI | None = None

    @property
    def offline(self) -> bool:
        return self.s.llm_offline or self.offline_handler is not None

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            if not self.s.nebius_api_key:
                raise LLMError("NEBIUS_API_KEY is not set (see docs/MANUAL_STEPS.md)")
            self._client = AsyncOpenAI(
                api_key=self.s.nebius_api_key,
                base_url=self.s.nebius_base_url,
                timeout=self.s.llm_timeout_s,
                max_retries=0,  # we own retry/backoff
                http_client=self._http_client,
            )
        return self._client

    def _model(self, tier: Tier) -> str:
        m = self.s.model_for(tier)
        if not m and not self.offline:
            raise LLMError(f"MODEL_{tier.upper()} is not set; run `make check-models`")
        return m or f"offline-{tier}"

    def _backoff(self, attempt: int) -> float:
        return float(min(20.0, 0.5 * (2**attempt)) * (0.5 + random.random()))  # noqa: S311

    def _record(self, tier: Tier, model: str, p: int, c: int, ms: float) -> None:
        self.tracker.record(UsageRecord(tier, model, p, c, ms, request_id_var.get()))

    async def chat(
        self,
        tier: Tier,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        json_mode: bool = False,
        extra: dict[str, Any] | None = None,
    ) -> ChatResult:
        model = self._model(tier)
        if self.offline_handler is not None:
            text = strip_think(self.offline_handler(tier, messages))
            self._record(
                tier, model, sum(len(m["content"]) // 4 for m in messages), len(text) // 4, 1
            )
            return ChatResult(text, 0, 0, 1.0, model)

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        if extra:
            kwargs["extra_body"] = extra

        last: Exception | None = None
        for attempt in range(self.s.llm_max_retries + 1):
            t0 = time.perf_counter()
            try:
                resp = await self.client.chat.completions.create(**kwargs)
            except RETRYABLE as e:
                last = e
                delay = self._backoff(attempt)
                log.warning("llm_retry", tier=tier, attempt=attempt, error=type(e).__name__)
                await self._sleep(delay)
                continue
            except openai.APIStatusError as e:
                raise LLMError(f"{tier} call failed: HTTP {e.status_code}: {e.message}") from e
            ms = (time.perf_counter() - t0) * 1000
            usage = resp.usage
            p = usage.prompt_tokens if usage else 0
            c = usage.completion_tokens if usage else 0
            text = strip_think(resp.choices[0].message.content or "")
            self._record(tier, model, p, c, ms)
            log.info("llm_call", tier=tier, model=model, prompt=p, completion=c, ms=round(ms))
            return ChatResult(text, p, c, ms, model)
        raise LLMError(f"{tier} call failed after retries: {last!r}")

    async def stream(
        self,
        tier: Tier,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> AsyncIterator[str]:
        """Yield visible text deltas; <think> content is suppressed even when streamed."""
        model = self._model(tier)
        if self.offline_handler is not None:
            text = strip_think(self.offline_handler(tier, messages))
            for word in re.findall(r"\S+\s*", text):
                yield word
            self._record(tier, model, 0, len(text) // 4, 1)
            return

        t0 = time.perf_counter()
        stream = await self.client.chat.completions.create(  # type: ignore[call-overload]
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            stream_options={"include_usage": True},
        )
        in_think = False
        buf = ""
        p = c = 0
        async for chunk in stream:
            if chunk.usage:
                p, c = chunk.usage.prompt_tokens, chunk.usage.completion_tokens
            if not chunk.choices:
                continue
            buf += chunk.choices[0].delta.content or ""
            while buf:
                if in_think:
                    end = buf.lower().find("</think>")
                    if end < 0:
                        buf = buf[-8:]  # keep tail in case the tag is split
                        break
                    buf, in_think = buf[end + 8 :], False
                    continue
                start = buf.lower().find("<think>")
                if start >= 0:
                    if start:
                        yield buf[:start]
                    buf, in_think = buf[start + 7 :], True
                    continue
                keep = 0
                for k in range(1, 7):  # hold back a possible partial "<think>"
                    if "<think>".startswith(buf[-k:].lower()):
                        keep = k
                if keep:
                    yield buf[:-keep]
                    buf = buf[-keep:]
                    break
                yield buf
                buf = ""
        if buf and not in_think:
            yield buf
        self._record(tier, model, p, c, (time.perf_counter() - t0) * 1000)

    async def structured(
        self,
        tier: Tier,
        messages: list[dict[str, str]],
        schema: type[T],
        *,
        max_repairs: int = 2,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> T:
        """JSON-schema prompt protocol: validate with pydantic, up to `max_repairs` repairs."""
        sys_note = (
            "Respond with ONLY a single JSON object matching this JSON schema. "
            "No prose, no markdown fences.\n" + json.dumps(schema.model_json_schema())
        )
        convo = [*messages, {"role": "system", "content": sys_note}]
        use_json_mode = self.s.structured_mode != "tools"
        err = ""
        for attempt in range(max_repairs + 1):
            res = await self.chat(
                tier, convo, temperature=temperature, max_tokens=max_tokens, json_mode=use_json_mode
            )
            try:
                return schema.model_validate(extract_json(res.text))
            except (StructuredOutputError, ValidationError, ValueError) as e:
                err = str(e)[:500]
                log.warning("structured_repair", tier=tier, attempt=attempt, error=err)
                convo = [
                    *convo,
                    {"role": "assistant", "content": res.text[:2000]},
                    {
                        "role": "user",
                        "content": "That was invalid: "
                        f"{err}\nReturn ONLY corrected JSON matching the schema.",
                    },
                ]
        raise StructuredOutputError(f"{schema.__name__}: invalid after repairs: {err}")

    async def list_models(self) -> list[str]:
        page = await self.client.models.list()
        return sorted(m.id for m in page.data)
