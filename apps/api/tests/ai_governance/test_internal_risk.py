from hypothesis import given, strategies as st

from ruleset.ai_governance.models import AISystemProfile
from ruleset.ai_governance.triage import evaluate_internal_risk


def profile(**changes: object) -> AISystemProfile:
    """Build one explicit fictional reviewer profile."""
    values = {
        "operator_roles": ["deployer"], "model_name": "test-model", "vendor": "test-vendor",
        "intended_users": ["analysts"], "affected_persons": [], "decision_impact": "Advisory",
        "data_categories": [], "geographies": ["US"], "external_access": False,
        "autonomy": "No execution", "tool_access": False, "human_oversight": "Every output",
        "decision_consequence": "minimal", "sensitive_data": False,
        "autonomy_level": "none", "human_review_coverage": "every_output",
    }
    values.update(changes)
    return AISystemProfile.model_validate(values)


# Reviewer-authored boundary profiles pin every rating boundary and each scoring condition.
CASES = [
    ({}, "low", 0),
    ({"affected_persons": ["customers"]}, "low", 1),
    ({"external_access": True}, "low", 1),
    ({"decision_consequence": "significant"}, "low", 2),
    ({"sensitive_data": True}, "low", 2),
    ({"tool_access": True}, "low", 2),
    ({"decision_consequence": "material", "external_access": True}, "low", 2),
    ({"autonomy_level": "assistive", "affected_persons": ["staff"]}, "low", 2),
    ({"human_review_coverage": "sampled", "external_access": True}, "low", 2),
    ({"decision_consequence": "significant", "external_access": True}, "medium", 3),
    ({"autonomy_level": "bounded", "tool_access": True}, "medium", 4),
    ({"sensitive_data": True, "external_access": True, "affected_persons": ["customers"]}, "medium", 4),
    ({"human_review_coverage": "none"}, "medium", 4),
    ({"decision_consequence": "severe"}, "medium", 4),
    ({"autonomy_level": "autonomous"}, "medium", 4),
    ({"decision_consequence": "significant", "tool_access": True, "external_access": True}, "medium", 5),
    ({"human_review_coverage": "exception_only", "sensitive_data": True, "affected_persons": ["customers"]}, "medium", 5),
    ({"autonomy_level": "assistive", "human_review_coverage": "sampled", "sensitive_data": True, "external_access": True}, "medium", 5),
    ({"decision_consequence": "severe", "tool_access": True}, "high", 6),
    ({"autonomy_level": "autonomous", "sensitive_data": True}, "high", 6),
    ({"human_review_coverage": "none", "external_access": True, "affected_persons": ["customers"]}, "high", 6),
    ({"decision_consequence": "significant", "autonomy_level": "bounded", "tool_access": True}, "high", 6),
    ({"decision_consequence": "severe", "sensitive_data": True, "external_access": True}, "high", 7),
    ({"autonomy_level": "autonomous", "tool_access": True, "affected_persons": ["customers"]}, "high", 7),
    ({"human_review_coverage": "none", "sensitive_data": True, "tool_access": True}, "high", 8),
    ({"decision_consequence": "severe", "autonomy_level": "bounded", "tool_access": True}, "high", 8),
    ({"decision_consequence": "severe", "autonomy_level": "autonomous", "external_access": True}, "critical", 9),
    ({"autonomy_level": "autonomous", "human_review_coverage": "none", "tool_access": True}, "critical", 10),
    ({"decision_consequence": "severe", "human_review_coverage": "none", "sensitive_data": True}, "critical", 10),
    ({"decision_consequence": "severe", "autonomy_level": "autonomous", "human_review_coverage": "none", "sensitive_data": True, "tool_access": True, "external_access": True, "affected_persons": ["customers"]}, "critical", 18),
]


def test_reviewer_authored_internal_risk_profiles() -> None:
    """Keep 30 explicit profiles stable across decision-table changes."""
    assert len(CASES) == 30
    for changes, expected_rating, expected_score in CASES:
        result = evaluate_internal_risk(profile(**changes))
        assert result.rating == expected_rating
        assert result.score == expected_score
        assert result.ruleset_version == 1


@given(st.sampled_from([
    "decision_consequence", "sensitive_data", "autonomy_level", "human_review_coverage"
]))
def test_missing_required_fact_never_guesses(field: str) -> None:
    """Return needs-review for every missing required fact."""
    result = evaluate_internal_risk(profile(**{field: None}))
    assert result.rating == "needs_review"
    assert result.score is None
    assert field in result.missing_facts
    assert result.fired_conditions == ()


def test_result_contains_exact_immutable_fact_snapshot() -> None:
    """Expose the exact validated facts and reject result mutation."""
    result = evaluate_internal_risk(profile(sensitive_data=True))
    assert result.facts["sensitive_data"] is True
    assert "sensitive_data" in result.fired_conditions
