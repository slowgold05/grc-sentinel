from typing import Any, Literal

import httpx
from pydantic import BaseModel, Field

from ruleset.generation.guardrails import RetryableModelError


class ClaudeResult(BaseModel):
    """Structured text and provider-reported usage from one Messages call."""

    text: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)


class _TextBlock(BaseModel):
    type: Literal["text"]
    text: str


class _Usage(BaseModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)


class _MessageResponse(BaseModel):
    content: list[_TextBlock]
    stop_reason: str
    usage: _Usage


async def call_claude_json(
    prompt: str,
    schema: dict[str, Any],
    *,
    api_key: str,
    model: str,
    max_tokens: int,
    transport: httpx.AsyncBaseTransport | None = None,
) -> ClaudeResult:
    """Call the pinned Anthropic endpoint with native JSON-schema output."""
    async with httpx.AsyncClient(
        base_url="https://api.anthropic.com", transport=transport, timeout=60
    ) as client:
        response = await client.post(
            "/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
            json={
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
                "output_config": {"format": {"type": "json_schema", "schema": schema}},
            },
        )
    if response.status_code in {429, 529}:
        raise RetryableModelError(f"Anthropic temporarily unavailable ({response.status_code})")
    response.raise_for_status()
    payload = _MessageResponse.model_validate(response.json())
    if payload.stop_reason not in {"end_turn", "stop_sequence"}:
        raise ValueError(f"Anthropic response stopped with {payload.stop_reason}")
    if len(payload.content) != 1:
        raise ValueError("Anthropic response must contain exactly one text block")
    return ClaudeResult(
        text=payload.content[0].text,
        input_tokens=payload.usage.input_tokens,
        output_tokens=payload.usage.output_tokens,
    )
