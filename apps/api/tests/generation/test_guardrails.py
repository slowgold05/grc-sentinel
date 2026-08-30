import asyncio

import pytest

from ruleset.generation.guardrails import (
    ModelGate,
    RetryableModelError,
    TokenBudget,
    TokenBudgetExceededError,
)


def test_budget_aborts_before_overrun_and_retry_is_bounded() -> None:
    budget = TokenBudget(limit=100)
    budget.reserve(80)
    with pytest.raises(TokenBudgetExceededError):
        budget.reserve(21)

    attempts = 0
    delays: list[float] = []

    async def operation() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RetryableModelError
        return "ok"

    async def sleep(delay: float) -> None:
        delays.append(delay)

    assert asyncio.run(ModelGate().call(operation, sleep=sleep)) == "ok"
    assert delays == [1, 2]
