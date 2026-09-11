from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from ruleset.ai_governance.models import AITriage, ApprovalDecision


def test_valid_ai_governance_contracts() -> None:
    """Accept a complete triage and a chronologically valid approval."""
    triage = AITriage(
        lifecycle_status="in_review",
        operator_roles=["deployer"],
        internal_risk="high",
        candidate_legal_status="candidate_transparency",
        explanation="The system interacts directly with users.",
    )
    decided_at = datetime.now(UTC)
    approval = ApprovalDecision(
        outcome="conditional",
        rationale="Deploy only with human review enabled.",
        decided_at=decided_at,
        expires_at=decided_at + timedelta(days=90),
    )

    assert triage.operator_roles[0].value == "deployer"
    assert approval.expires_at > approval.decided_at


@pytest.mark.parametrize(
    ("model", "payload"),
    [
        (
            AITriage,
            {
                "lifecycle_status": "unknown",
                "operator_roles": ["deployer"],
                "internal_risk": "high",
                "candidate_legal_status": "candidate_minimal",
                "explanation": "Invalid lifecycle.",
            },
        ),
        (
            AITriage,
            {
                "lifecycle_status": "in_review",
                "operator_roles": ["deployer"],
                "internal_risk": "high",
                "candidate_legal_status": "needs_review",
                "explanation": "Missing facts were not identified.",
            },
        ),
        (
            AITriage,
            {
                "lifecycle_status": "in_review",
                "operator_roles": ["deployer"],
                "internal_risk": "high",
                "candidate_legal_status": "candidate_minimal",
                "explanation": "x" * 2_001,
            },
        ),
        (
            ApprovalDecision,
            {
                "outcome": "approved",
                "rationale": "Dates are reversed.",
                "decided_at": "2026-09-11T12:00:00Z",
                "expires_at": "2026-09-10T12:00:00Z",
            },
        ),
        (
            ApprovalDecision,
            {
                "outcome": "approved",
                "rationale": "Invalid date.",
                "decided_at": "not-a-date",
            },
        ),
    ],
)
def test_invalid_ai_governance_contracts(model: type, payload: dict[str, object]) -> None:
    """Reject unknown, inconsistent, excessive, and invalid values."""
    with pytest.raises(ValidationError):
        model.model_validate(payload)
