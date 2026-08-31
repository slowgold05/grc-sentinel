import asyncio

import httpx
import pytest

from ruleset.generation.guardrails import RetryableModelError
from ruleset.generation.openai_compatible_client import call_model_json


def test_calls_compatible_endpoint_with_schema_auth_and_usage() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://openrouter.ai/api/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer secret"
        assert b"secret" not in request.content
        assert b"json_schema" in request.content
        assert b'"reasoning_effort":"low"' in request.content
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": '{"ok":true}'}, "finish_reason": "stop"}
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 4},
            },
        )

    result = asyncio.run(
        call_model_json(
            "prompt",
            {"type": "object"},
            base_url="https://openrouter.ai/api/v1",
            api_key="secret",
            model="z-ai/glm-5.3-flash",
            max_tokens=100,
            transport=httpx.MockTransport(handler),
        )
    )
    assert (result.input_tokens, result.output_tokens) == (10, 4)

    with pytest.raises(RetryableModelError):
        asyncio.run(
            call_model_json(
                "prompt",
                {"type": "object"},
                base_url="http://localhost:11434/v1",
                model="test-model",
                max_tokens=100,
                transport=httpx.MockTransport(lambda _: httpx.Response(500)),
            )
        )
