import asyncio

import httpx
import pytest

from ruleset.generation.anthropic_client import call_claude_json
from ruleset.generation.guardrails import RetryableModelError


def test_calls_fixed_endpoint_without_exposing_key_in_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).startswith("https://api.anthropic.com/v1/messages")
        assert request.headers["x-api-key"] == "secret"
        assert b"secret" not in request.content
        assert b"output_config" in request.content
        return httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": '{"ok":true}'}],
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 10, "output_tokens": 4},
            },
        )

    result = asyncio.run(
        call_claude_json(
            "prompt",
            {"type": "object"},
            api_key="secret",
            model="test-model",
            max_tokens=100,
            transport=httpx.MockTransport(handler),
        )
    )
    assert (result.input_tokens, result.output_tokens) == (10, 4)

    async def throttled() -> None:
        await call_claude_json(
            "prompt",
            {"type": "object"},
            api_key="secret",
            model="test-model",
            max_tokens=100,
            transport=httpx.MockTransport(lambda _: httpx.Response(429)),
        )

    with pytest.raises(RetryableModelError):
        asyncio.run(throttled())
