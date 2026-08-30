from typing import Literal

from pydantic import BaseModel, Field, JsonValue, RootModel


class CompanyFacts(RootModel[dict[str, JsonValue]]):
    """Validated company facts consumed by deterministic rules."""


class Condition(BaseModel):
    """One comparison against a named company fact."""

    fact: str = Field(min_length=1)
    op: Literal["equals", "includes", "gte", "lte"]
    value: JsonValue


class Rule(BaseModel):
    """A versioned regulation applicability rule."""

    rule_id: str = Field(min_length=1)
    regulation: str = Field(min_length=1)
    all_conditions: list[Condition] = Field(alias="all", min_length=1)
    explanation: str = Field(min_length=1)
    citations: list[str] = Field(min_length=1)
    version: int = Field(ge=1)


class Determination(BaseModel):
    """Immutable evidence explaining why one regulation applies."""

    rule_id: str
    rule_version: int
    regulation: str
    explanation: str
    citations: list[str]
    facts: dict[str, JsonValue]

