from pydantic import BaseModel, ConfigDict, Field, JsonValue


class RetrievedControl(BaseModel):
    """Control context explicitly made available to generation."""

    control_id: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=20_000)
    parameters: dict[str, JsonValue] = Field(default_factory=dict)


class GeneratedStatement(BaseModel):
    """One untrusted structured policy statement from the model."""

    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=10_000)
    control_ids: list[str] = Field(min_length=1, max_length=50)
    parameters_used: list[str] = Field(default_factory=list, max_length=50)


class GenerationOutput(BaseModel):
    """Length-capped structured model output."""

    model_config = ConfigDict(extra="forbid")
    statements: list[GeneratedStatement] = Field(min_length=1, max_length=100)


class CitationVerdict(BaseModel):
    """Deterministic verdict over generated control references."""

    accepted: bool
    invalid_control_ids: list[str]
