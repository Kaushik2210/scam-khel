import httpx2 as httpx
import pytest
from openai import DefaultAsyncHttpxClient
from pydantic import BaseModel

from app.config import Settings
from app.llm.client import (
    LLMClient,
    LLMError,
    StructuredOutputError,
    extract_json,
    strip_think,
)
from app.llm.usage import UsageTracker

BASE = "https://example.test/v1/"


class Out(BaseModel):
    a: int


class Route:
    """Queue of canned responses served via httpx2.MockTransport (the transport openai uses)."""

    def __init__(self, responses: list[httpx.Response]) -> None:
        self.queue = list(responses)
        self.call_count = 0
        self.bodies: list[bytes] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.call_count += 1
        self.bodies.append(request.content)
        return self.queue.pop(0) if len(self.queue) > 1 else self.queue[0]


def mk(route: Route, **kw) -> tuple[LLMClient, UsageTracker]:
    t = UsageTracker()
    s = Settings(
        _env_file=None,
        nebius_api_key="k",
        nebius_base_url=BASE,
        model_fast="f",
        model_mid="m",
        model_deep="d",
        llm_max_retries=2,
        **kw,
    )

    async def nosleep(_: float) -> None:
        return None

    http = DefaultAsyncHttpxClient(transport=httpx.MockTransport(route))
    return LLMClient(s, tracker=t, sleep=nosleep, http_client=http), t


def completion(content: str) -> dict:
    return {
        "id": "x",
        "object": "chat.completion",
        "created": 0,
        "model": "f",
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": content},
            }
        ],
        "usage": {"prompt_tokens": 5, "completion_tokens": 7, "total_tokens": 12},
    }


def test_strip_think():
    assert strip_think("<think>hmm\nx</think>\nhello") == "hello"
    assert strip_think("reasoning only</think>answer") == "answer"
    assert strip_think("plain") == "plain"


def test_extract_json_variants():
    assert extract_json('<think>x</think>```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('Sure! {"a": 2} done') == {"a": 2}
    with pytest.raises(StructuredOutputError):
        extract_json("nothing")


async def test_chat_routes_tier_and_records_usage():
    route = Route([httpx.Response(200, json=completion("<think>z</think>hi"))])
    c, t = mk(route)
    r = await c.chat("mid", [{"role": "user", "content": "yo"}])
    assert r.text == "hi"
    assert b'"model":"m"' in route.bodies[0].replace(b" ", b"")
    s = t.summary()
    assert s["mid"]["calls"] == 1 and s["mid"]["completion_tokens"] == 7
    assert s["fast"]["calls"] == 0


async def test_retries_on_429_then_succeeds():
    c, _ = mk(
        Route(
            [
                httpx.Response(429, json={"error": {"message": "slow"}}),
                httpx.Response(503, json={"error": {"message": "down"}}),
                httpx.Response(200, json=completion("ok")),
            ]
        )
    )
    assert (await c.chat("fast", [{"role": "user", "content": "x"}])).text == "ok"


async def test_gives_up_after_retries():
    c, _ = mk(Route([httpx.Response(500, json={"error": {"message": "boom"}})]))
    with pytest.raises(LLMError):
        await c.chat("fast", [{"role": "user", "content": "x"}])


async def test_4xx_not_retried():
    route = Route([httpx.Response(400, json={"error": {"message": "bad"}})])
    c, _ = mk(route)
    with pytest.raises(LLMError):
        await c.chat("fast", [{"role": "user", "content": "x"}])
    assert route.call_count == 1


async def test_structured_repairs_then_validates():
    route = Route(
        [
            httpx.Response(200, json=completion("not json")),
            httpx.Response(200, json=completion('{"a": "x"}')),
            httpx.Response(200, json=completion('{"a": 3}')),
        ]
    )
    c, _ = mk(route)
    out = await c.structured("fast", [{"role": "user", "content": "x"}], Out)
    assert out.a == 3 and route.call_count == 3


async def test_structured_fails_after_two_repairs():
    c, _ = mk(Route([httpx.Response(200, json=completion("nope"))]))
    with pytest.raises(StructuredOutputError):
        await c.structured("fast", [{"role": "user", "content": "x"}], Out)


async def test_offline_handler_and_stream_strips_think():
    t = UsageTracker()
    s = Settings(_env_file=None, model_mid="m")
    c = LLMClient(s, tracker=t, offline_handler=lambda tier, msgs: "<think>a</think>namaste ji")
    out = [x async for x in c.stream("mid", [{"role": "user", "content": "x"}])]
    assert out == ["namaste ", "ji"]
    assert t.summary()["mid"]["calls"] == 1


def test_missing_key_is_clear_error():
    c = LLMClient(Settings(_env_file=None, model_fast="f"))
    with pytest.raises(LLMError, match="NEBIUS_API_KEY"):
        _ = c.client


def tool_completion(args_json: str) -> dict:
    return {
        "id": "tc1",
        "object": "chat.completion",
        "created": 0,
        "model": "f",
        "choices": [
            {
                "index": 0,
                "finish_reason": "tool_calls",
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "Out", "arguments": args_json},
                        }
                    ],
                },
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18},
    }


async def test_structured_native_tool_calling_success():
    route = Route([httpx.Response(200, json=tool_completion('{"a": 42}'))])
    c, t = mk(route, structured_mode="tools")
    out = await c.structured("fast", [{"role": "user", "content": "x"}], Out)
    assert out.a == 42
    assert route.call_count == 1
    assert b'"tools":' in route.bodies[0]


async def test_structured_native_tool_calling_falls_back_to_json_prompt():
    route = Route(
        [
            # First attempt (native tool calling) returns 400 (e.g. tools unsupported)
            httpx.Response(400, json={"error": {"message": "tools unsupported by model"}}),
            # Fallback to JSON-prompt succeeds
            httpx.Response(200, json=completion('{"a": 99}')),
        ]
    )
    c, t = mk(route, structured_mode="tools")
    out = await c.structured("fast", [{"role": "user", "content": "x"}], Out)
    assert out.a == 99
    assert route.call_count == 2


async def test_disable_thinking_sends_template_kwarg_only_when_enabled():
    on = Route([httpx.Response(200, json=completion("hi"))])
    c, _ = mk(on, llm_disable_thinking=True)
    await c.chat("fast", [{"role": "user", "content": "yo"}])
    assert b'"enable_thinking":false' in on.bodies[0].replace(b" ", b"")

    off = Route([httpx.Response(200, json=completion("hi"))])
    c2, _ = mk(off)
    await c2.chat("fast", [{"role": "user", "content": "yo"}])
    assert b"enable_thinking" not in off.bodies[0]
