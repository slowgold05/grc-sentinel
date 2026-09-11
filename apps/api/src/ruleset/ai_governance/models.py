from datetime import date, datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

ShortLabel = Annotated[str, Field(min_length=1, max_length=200)]


class LifecycleStatus(StrEnum):
    """Allowed lifecycle states for an inventoried AI system."""

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    DEPLOYED = "deployed"
    SUSPENDED = "suspended"
    RETIRED = "retired"


class OperatorRole(StrEnum):
    """Organization roles kept distinct for candidate legal review."""

    PROVIDER = "provider"
    DEPLOYER = "deployer"
    IMPORTER = "importer"
    DISTRIBUTOR = "distributor"
    PRODUCT_MANUFACTURER = "product_manufacturer"
    GPAI_PROVIDER = "gpai_provider"
    UNKNOWN = "unknown"


class InternalRiskRating(StrEnum):
    """Internal prioritization values that are not legal classifications."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    NEEDS_REVIEW = "needs_review"


class DecisionConsequence(StrEnum):
    """Organization-defined consequence if an AI-assisted decision is wrong."""

    MINIMAL = "minimal"
    MATERIAL = "material"
    SIGNIFICANT = "significant"
    SEVERE = "severe"


class AutonomyLevel(StrEnum):
    """Structured execution authority for internal risk prioritization."""

    NONE = "none"
    ASSISTIVE = "assistive"
    BOUNDED = "bounded"
    AUTONOMOUS = "autonomous"


class HumanReviewCoverage(StrEnum):
    """Structured human-review coverage for internal risk prioritization."""

    EVERY_OUTPUT = "every_output"
    SAMPLED = "sampled"
    EXCEPTION_ONLY = "exception_only"
    NONE = "none"


class CandidateLegalStatus(StrEnum):
    """Non-final statuses emitted by candidate legal triage."""

    PROHIBITED = "candidate_prohibited"
    HIGH_RISK = "candidate_high_risk"
    TRANSPARENCY = "candidate_transparency"
    MINIMAL = "candidate_minimal"
    NOT_APPLICABLE = "not_applicable"
    NEEDS_REVIEW = "needs_review"


class ApprovalOutcome(StrEnum):
    """Human-only governance decision outcomes."""

    APPROVED = "approved"
    REJECTED = "rejected"
    CONDITIONAL = "conditional"


class EvaluationResult(StrEnum):
    """Stored verdicts for versioned AI evaluations."""

    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"


class IncidentSeverity(StrEnum):
    """Organization-defined AI incident severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AITriage(BaseModel):
    """Validated deterministic triage result with explicit uncertainty."""

    model_config = ConfigDict(extra="forbid")
    lifecycle_status: LifecycleStatus
    operator_roles: list[OperatorRole] = Field(min_length=1, max_length=7)
    internal_risk: InternalRiskRating
    candidate_legal_status: CandidateLegalStatus
    explanation: str = Field(min_length=1, max_length=2_000)
    missing_facts: list[str] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def uncertainty_matches_missing_facts(self) -> "AITriage":
        """Require missing facts exactly when legal triage needs review."""
        needs_review = self.candidate_legal_status == CandidateLegalStatus.NEEDS_REVIEW
        if needs_review != bool(self.missing_facts):
            raise ValueError("needs_review must correspond to one or more missing facts")
        return self


class ApprovalDecision(BaseModel):
    """Validated append-only human approval payload."""

    model_config = ConfigDict(extra="forbid")
    outcome: ApprovalOutcome
    rationale: str = Field(min_length=1, max_length=10_000)
    decided_at: datetime
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def expiry_follows_decision(self) -> "ApprovalDecision":
        """Reject an approval that expires before it exists."""
        if self.expires_at is not None and self.expires_at <= self.decided_at:
            raise ValueError("expires_at must be later than decided_at")
        return self


class EvaluationVerdict(BaseModel):
    """Validated summary of an immutable evaluation run."""

    model_config = ConfigDict(extra="forbid")
    result: EvaluationResult
    evaluation_id: str = Field(min_length=1, max_length=100)
    summary: str = Field(min_length=1, max_length=2_000)
    evaluated_at: datetime


class IncidentClassification(BaseModel):
    """Validated human-owned incident classification."""

    model_config = ConfigDict(extra="forbid")
    severity: IncidentSeverity
    summary: str = Field(min_length=1, max_length=10_000)
    regulatory_review_required: bool


class AISystemProfile(BaseModel):
    """Validated facts describing one inventoried AI system."""

    model_config = ConfigDict(extra="forbid")
    operator_roles: list[OperatorRole] = Field(min_length=1, max_length=7)
    model_name: str = Field(min_length=1, max_length=200)
    vendor: str = Field(min_length=1, max_length=200)
    intended_users: list[ShortLabel] = Field(min_length=1, max_length=50)
    affected_persons: list[ShortLabel] = Field(default_factory=list, max_length=50)
    decision_impact: str = Field(min_length=1, max_length=1_000)
    data_categories: list[ShortLabel] = Field(default_factory=list, max_length=50)
    geographies: list[ShortLabel] = Field(default_factory=list, max_length=50)
    external_access: bool
    autonomy: str = Field(min_length=1, max_length=200)
    tool_access: bool
    human_oversight: str = Field(min_length=1, max_length=2_000)
    decision_consequence: DecisionConsequence | None = None
    sensitive_data: bool | None = None
    autonomy_level: AutonomyLevel | None = None
    human_review_coverage: HumanReviewCoverage | None = None


class InternalRiskResult(BaseModel):
    """Explainable internal prioritization result; never a legal classification."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    ruleset_id: str
    ruleset_version: int
    rating: InternalRiskRating
    score: int | None
    facts: dict[str, object]
    fired_conditions: tuple[str, ...]
    missing_facts: tuple[str, ...]


class AISystemCreate(BaseModel):
    """Validated request for an engagement-owned AI system."""

    model_config = ConfigDict(extra="forbid")
    engagement_id: UUID
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10_000)
    owner: str = Field(min_length=1, max_length=200)
    business_purpose: str = Field(min_length=1, max_length=2_000)
    profile: AISystemProfile
    deployment_date: date | None = None
    next_review_date: date | None = None

    @model_validator(mode="after")
    def review_follows_deployment(self) -> "AISystemCreate":
        """Reject a review date earlier than the deployment date."""
        if (
            self.deployment_date is not None
            and self.next_review_date is not None
            and self.next_review_date < self.deployment_date
        ):
            raise ValueError("next_review_date cannot precede deployment_date")
        return self


class AISystemStateUpdate(BaseModel):
    """Validated lifecycle-state change request."""

    model_config = ConfigDict(extra="forbid")
    status: LifecycleStatus


class AISystemRecord(AISystemCreate):
    """Stored AI system inventory record."""

    id: UUID
    status: LifecycleStatus
    created_at: datetime
    updated_at: datetime
