from typing import Any

import httpx
from pydantic import BaseModel, Field

from ruleset.generation.guardrails import RetryableModelError


class ModelResult(BaseModel):
    """Structured text and provider-reported usage from one chat completion."""

    text: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)


class _Message(BaseModel):
    content: str


class _Choice(BaseModel):
    message: _Message
    finish_reason: str


class _Usage(BaseModel):
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)


class _ChatResponse(BaseModel):
    choices: list[_Choice]
    usage: _Usage


async def call_model_json(
    prompt: str,
    schema: dict[str, Any],
    *,
    base_url: str,
    model: str,
    max_tokens: int,
    api_key: str | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> ModelResult:
    """Call an OpenAI-compatible model endpoint with a JSON schema."""
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    async with httpx.AsyncClient(
        base_url=base_url, headers=headers, transport=transport, timeout=120
    ) as client:
        response = await client.post(
            "/chat/completions",
            json={
                "model": model,
                "max_tokens": max_tokens,
                "reasoning_effort": "low",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {"name": "ruleset_response", "schema": schema, "strict": True},
                },
            },
        )
    if response.status_code == 429 or response.status_code >= 500:
        raise RetryableModelError(f"Model endpoint temporarily unavailable ({response.status_code})")
    response.raise_for_status()
    payload = _ChatResponse.model_validate(response.json())
    if len(payload.choices) != 1:
        raise ValueError("Model response must contain exactly one choice")
    choice = payload.choices[0]
    if choice.finish_reason not in {"stop", "length"}:
        raise ValueError(f"Model response stopped with {choice.finish_reason}")
    return ModelResult(
        text=choice.message.content,
        input_tokens=payload.usage.prompt_tokens,
        output_tokens=payload.usage.completion_tokens,
    )
