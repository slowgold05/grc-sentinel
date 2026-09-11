from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Literal
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


class GovernanceDecisionType(StrEnum):
    """Human-owned AI lifecycle decision categories."""

    ASSESSMENT = "assessment"
    DEPLOYMENT = "deployment"
    MATERIAL_CHANGE = "material_change"
    EXCEPTION = "exception"
    RETIREMENT = "retirement"
    RESIDUAL_RISK = "residual_risk"
    LEGAL_REVIEW = "legal_review"


class EvaluationResult(StrEnum):
    """Stored verdicts for versioned AI evaluations."""

    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"


class EvaluationType(StrEnum):
    """Supported AI evaluation risk dimensions."""

    TASK_PERFORMANCE = "task_performance"
    ROBUSTNESS = "robustness"
    PROMPT_INJECTION = "prompt_injection"
    PRIVACY_LEAKAGE = "privacy_leakage"
    GROUNDEDNESS = "groundedness"
    HARMFUL_OUTPUT = "harmful_output"
    CONTEXTUAL_FAIRNESS = "contextual_fairness"
    OVERSIGHT_EFFECTIVENESS = "oversight_effectiveness"
    RELIABILITY = "reliability"


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


class GovernanceDecisionCreate(BaseModel):
    """Validated request for one append-only governance decision."""

    model_config = ConfigDict(extra="forbid")
    decision_type: GovernanceDecisionType
    outcome: ApprovalOutcome
    rationale: str = Field(min_length=1, max_length=10_000)
    assessment_version_id: UUID | None = None
    expires_at: datetime | None = None
    expected_latest_decision_id: UUID | None = None


class GovernanceDecisionRecord(GovernanceDecisionCreate):
    """Stored decision with verified actor and supersession link."""

    id: UUID
    ai_system_id: UUID
    supersedes_id: UUID | None
    decided_by: str
    decided_at: datetime


class DeploymentGateFacts(BaseModel):
    """Explicit current facts consumed by the pure deployment gate."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    assessment_current: bool
    assessment_approved: bool
    residual_risk_decided: bool
    residual_risk_accepted: bool
    evaluation_required: bool
    evaluation_current: bool
    evaluation_passed: bool
    exception_required: bool
    exception_valid: bool
    legal_review_required: bool
    legal_review_approved: bool


class DeploymentGateResult(BaseModel):
    """Deterministic blocker list that no model may alter."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    allowed: bool
    blockers: tuple[str, ...]


class EvaluationVerdict(BaseModel):
    """Validated summary of an immutable evaluation run."""

    model_config = ConfigDict(extra="forbid")
    result: EvaluationResult
    evaluation_id: str = Field(min_length=1, max_length=100)
    summary: str = Field(min_length=1, max_length=2_000)
    evaluated_at: datetime


class EvaluationDefinitionCreate(BaseModel):
    """Immutable versioned evaluation definition input."""

    model_config = ConfigDict(extra="forbid")
    evaluation_type: EvaluationType
    name: str = Field(min_length=1, max_length=200)
    dataset_name: str = Field(min_length=1, max_length=200)
    dataset_version: str = Field(min_length=1, max_length=100)
    population_context: str = Field(min_length=1, max_length=2_000)
    metric_name: str = Field(min_length=1, max_length=200)
    metric_direction: Literal["higher_is_better", "lower_is_better"]
    threshold: float
    owner: str = Field(min_length=1, max_length=200)
    cadence: str = Field(min_length=1, max_length=200)
    limitations: str = Field(min_length=1, max_length=2_000)


class EvaluationDefinitionRecord(EvaluationDefinitionCreate):
    """Stored definition with approval and latest-measurement state."""

    id: UUID
    ai_system_id: UUID
    version: int
    created_by: str
    created_at: datetime
    threshold_approved_by: str | None = None
    latest_result: Literal["pass", "fail"] | None = None


class ThresholdApprovalCreate(BaseModel):
    """Human threshold-approval rationale."""

    model_config = ConfigDict(extra="forbid")
    rationale: str = Field(min_length=1, max_length=10_000)


class EvaluationRunCreate(BaseModel):
    """Measured evaluation output bound to model and configuration versions."""

    model_config = ConfigDict(extra="forbid")
    model_version: str = Field(min_length=1, max_length=200)
    configuration_version: str = Field(min_length=1, max_length=200)
    measured_value: float
    summary: str = Field(min_length=1, max_length=2_000)


class EvaluationRunRecord(EvaluationRunCreate):
    """Append-only deterministic evaluation verdict."""

    id: UUID
    definition_id: UUID
    definition_version: int
    dataset_version: str
    result: Literal["pass", "fail"]
    run_by: str
    tested_at: datetime


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


class EUCandidateFacts(BaseModel):
    """Reviewer-supplied facts for a non-production EU AI Act candidate assessment."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    geography: ShortLabel
    operator_role: OperatorRole
    intended_purpose: str = Field(min_length=1, max_length=2_000)
    affected_persons: tuple[ShortLabel, ...] = Field(default_factory=tuple, max_length=50)
    territorial_scope_confirmed: bool | None = None
    prohibited_practice_indicators: tuple[ShortLabel, ...] = Field(default_factory=tuple, max_length=50)
    prohibited_review_complete: bool | None = None
    annex_i_or_iii_category: ShortLabel | None = None
    high_risk_path_confirmed: bool | None = None
    gpai_role_confirmed: bool | None = None
    transparency_scenario: ShortLabel | None = None
    transparency_review_complete: bool | None = None


class EUCandidateResult(BaseModel):
    """Test-only EU AI Act candidate route, not a legal determination."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    ruleset_id: str
    ruleset_version: int
    source_identifier: str
    status: CandidateLegalStatus
    fired_condition: str | None
    missing_facts: tuple[str, ...]


class AIAssuranceObjectiveCreate(BaseModel):
    """User-selected AI assurance objective; never an applicable-law claim."""

    model_config = ConfigDict(extra="forbid")
    framework: Literal["nist_ai_rmf", "iso_42001", "singapore_model_ai_governance"]
    basis: Literal["customer_contract", "company_strategy", "regulator_request"]
    scope: str = Field(min_length=1, max_length=2_000)
    target_date: date | None = None


class AIAssuranceObjective(AIAssuranceObjectiveCreate):
    """Stored AI objective with pinned provenance and selector."""

    id: UUID
    ai_system_id: UUID
    source_version: str
    objective_type: Literal["voluntary", "certifiable"]
    selected_by: str
    created_at: datetime


class AIImpactContent(BaseModel):
    """Structured impact-assessment domains; blank fields remain review blockers."""

    model_config = ConfigDict(extra="forbid")
    purpose_limitations: str = Field(default="", max_length=10_000)
    stakeholders: str = Field(default="", max_length=10_000)
    benefits_harms: str = Field(default="", max_length=10_000)
    data_provenance: str = Field(default="", max_length=10_000)
    privacy: str = Field(default="", max_length=10_000)
    contextual_fairness: str = Field(default="", max_length=10_000)
    explainability: str = Field(default="", max_length=10_000)
    security: str = Field(default="", max_length=10_000)
    robustness: str = Field(default="", max_length=10_000)
    human_oversight: str = Field(default="", max_length=10_000)
    vendor_reliance: str = Field(default="", max_length=10_000)
    misuse: str = Field(default="", max_length=10_000)
    incident_response: str = Field(default="", max_length=10_000)
    monitoring: str = Field(default="", max_length=10_000)
    decommissioning: str = Field(default="", max_length=10_000)


class AIImpactDraft(BaseModel):
    """Editable current assessment draft."""

    id: UUID
    ai_system_id: UUID
    content: AIImpactContent
    author: str
    updated_at: datetime


class AIImpactVersion(BaseModel):
    """Immutable submitted assessment snapshot."""

    id: UUID
    ai_system_id: UUID
    version: int
    content: AIImpactContent
    status: Literal["complete", "needs_review"]
    missing_facts: tuple[str, ...]
    author: str
    reviewer: str | None
    source_versions: dict[str, str]
    created_at: datetime


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
