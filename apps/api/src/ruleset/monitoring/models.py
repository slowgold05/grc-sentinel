from datetime import datetime
from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, JsonValue


class TestResult(BaseModel):
    """Validated observation returned by a read-only control test."""

    model_config = ConfigDict(extra="forbid")
    status: Literal["pass", "fail", "error"]
    observed: dict[str, JsonValue]
    tested_at: datetime


@runtime_checkable
class ControlTest(Protocol):
    """Minimal connector-independent contract for live control checks."""

    test_id: str
    control_ids: list[str]

    def run(self, connection: object) -> TestResult: ...
