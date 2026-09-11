import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeVar


T = TypeVar("T")


class TokenBudgetExceededError(RuntimeError):
    """Raised before a model call would exceed its engagement budget."""


class CostBudgetExceededError(RuntimeError):
    """Raised before a hosted model call would exceed its cost budget."""


class RetryableModelError(RuntimeError):
    """Raised for provider throttling or temporary unavailability."""


@dataclass
class TokenBudget:
    """Conservative in-memory token reservation for one generation run."""

    limit: int
    reserved: int = 0

    def reserve(self, tokens: int) -> None:
        """Reserve estimated input plus maximum output tokens before a call."""
        if tokens < 0 or self.reserved + tokens > self.limit:
            raise TokenBudgetExceededError("engagement token budget exceeded")
        self.reserved += tokens


@dataclass
class CostBudget:
    """Conservative hosted-model cost reservation in millionths of a US dollar."""

    limit_microusd: int
    reserved_microusd: int = 0

    def reserve(self, estimated_microusd: int) -> None:
        """Reserve estimated call cost before contacting a hosted provider."""
        if estimated_microusd < 0 or self.reserved_microusd + estimated_microusd > self.limit_microusd:
            raise CostBudgetExceededError("engagement cost budget exceeded")
        self.reserved_microusd += estimated_microusd


class ModelGate:
    """Cap concurrent calls and retry only explicitly temporary failures."""

    def __init__(self, concurrency: int = 3, attempts: int = 3) -> None:
        if concurrency < 1 or attempts < 1:
            raise ValueError("concurrency and attempts must be positive")
        self._semaphore = asyncio.Semaphore(concurrency)
        self.attempts = attempts

    async def call(
        self,
        operation: Callable[[], Awaitable[T]],
        *,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> T:
        """Run one operation with bounded exponential backoff."""
        async with self._semaphore:
            for attempt in range(self.attempts):
                try:
                    return await operation()
                except RetryableModelError:
                    if attempt + 1 == self.attempts:
                        raise
                    await sleep(2**attempt)
        raise RuntimeError("unreachable")
