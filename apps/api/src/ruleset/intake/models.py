from pydantic import BaseModel, Field, field_validator

from ruleset.osint.dns_posture import normalize_domain


class CompanyIntake(BaseModel):
    """Validated company facts collected by the intake wizard."""

    company_name: str = Field(min_length=1, max_length=200)
    domain: str
    employee_count: int = Field(ge=1)
    geos: list[str] = Field(default_factory=list)
    data_types: list[str] = Field(default_factory=list)
    sends_external_email: bool | None = None
    cloud_providers: list[str] = Field(default_factory=list)

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, value: str) -> str:
        """Store domains in their validated canonical form."""
        return normalize_domain(value)
