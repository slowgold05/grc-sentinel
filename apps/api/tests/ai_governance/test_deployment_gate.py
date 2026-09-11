from datetime import UTC, datetime, timedelta

import pytest

from ruleset.ai_governance.deployment_gate import evaluate_deployment_gate
from ruleset.ai_governance.models import DeploymentGateFacts, GovernanceDecisionCreate


ALL_CLEAR = {
    "assessment_current": True,
    "assessment_approved": True,
    "residual_risk_decided": True,
    "residual_risk_accepted": True,
    "evaluation_required": True,
    "evaluation_current": True,
    "evaluation_passed": True,
    "exception_required": True,
    "exception_expires_at": datetime.now(UTC) + timedelta(days=1),
    "evaluated_at": datetime.now(UTC),
    "legal_review_required": True,
    "legal_review_approved": True,
}


@pytest.mark.parametrize(
    ("changes", "blocker"),
    [
        ({"assessment_current": False}, "current_assessment_missing"),
        ({"assessment_approved": False}, "current_assessment_not_approved"),
        ({"residual_risk_decided": False}, "residual_risk_decision_missing"),
        ({"residual_risk_accepted": False}, "residual_risk_not_accepted"),
        ({"evaluation_current": False}, "current_evaluation_missing"),
        ({"evaluation_passed": False}, "required_evaluation_failed"),
        (
            {"exception_expires_at": datetime.now(UTC) - timedelta(seconds=1)},
            "valid_exception_missing",
        ),
        ({"legal_review_approved": False}, "legal_review_not_approved"),
    ],
)
def test_each_deployment_blocker(changes: dict[str, bool], blocker: str) -> None:
    """Return the exact blocker for each failed prerequisite."""
    result = evaluate_deployment_gate(DeploymentGateFacts(**(ALL_CLEAR | changes)))
    assert not result.allowed
    assert blocker in result.blockers


def test_all_clear_and_optional_checks() -> None:
    """Allow deployment when every required check is current and accepted."""
    facts = ALL_CLEAR | {
        "evaluation_required": False,
        "evaluation_current": False,
        "evaluation_passed": False,
        "exception_required": False,
        "exception_expires_at": None,
        "legal_review_required": False,
        "legal_review_approved": False,
    }
    result = evaluate_deployment_gate(DeploymentGateFacts(**facts))
    assert result.allowed
    assert result.blockers == ()


def test_accepted_exception_requires_complete_time_limited_terms() -> None:
    with pytest.raises(ValueError, match="expiry, owner, and compensating controls"):
        GovernanceDecisionCreate(
            decision_type="exception", outcome="conditional", rationale="Temporary risk"
        )


def test_returns_all_blockers_without_model_interpretation() -> None:
    """Return every independent blocker in stable rule order."""
    result = evaluate_deployment_gate(
        DeploymentGateFacts(
            **{
                **{
                    key: False
                    for key in ALL_CLEAR
                    if key not in {"evaluated_at", "exception_expires_at"}
                },
                "evaluated_at": datetime.now(UTC),
                "exception_expires_at": None,
            }
        )
    )
    assert result.blockers == (
        "current_assessment_missing",
        "residual_risk_decision_missing",
    )
