from hypothesis import given, strategies as st

from ruleset.ai_governance.eu_candidate import evaluate_eu_candidate
from ruleset.ai_governance.models import EUCandidateFacts
from ruleset.main import app


def facts(**changes: object) -> EUCandidateFacts:
    """Build explicit fictional facts reviewed for candidate routing."""
    values = {
        "geography": "European Union", "operator_role": "deployer",
        "intended_purpose": "Draft text for a person to review", "affected_persons": (),
        "territorial_scope_confirmed": True, "prohibited_practice_indicators": (),
        "prohibited_review_complete": True, "annex_i_or_iii_category": None,
        "high_risk_path_confirmed": False, "gpai_role_confirmed": False,
        "transparency_scenario": None, "transparency_review_complete": True,
    }
    values.update(changes)
    return EUCandidateFacts.model_validate(values)


CASES = [
    ({"territorial_scope_confirmed": False}, "not_applicable"),
    ({"territorial_scope_confirmed": False, "operator_role": "provider"}, "not_applicable"),
    ({"territorial_scope_confirmed": False, "gpai_role_confirmed": True}, "not_applicable"),
    ({"territorial_scope_confirmed": False, "affected_persons": ("staff",)}, "not_applicable"),
    ({"territorial_scope_confirmed": False, "transparency_scenario": "chatbot"}, "not_applicable"),
    ({"prohibited_practice_indicators": ("reviewer indicator A",)}, "candidate_prohibited"),
    ({"prohibited_practice_indicators": ("reviewer indicator B",), "operator_role": "provider"}, "candidate_prohibited"),
    ({"prohibited_practice_indicators": ("indicator A", "indicator B")}, "candidate_prohibited"),
    ({"prohibited_practice_indicators": ("indicator",), "high_risk_path_confirmed": True}, "candidate_prohibited"),
    ({"prohibited_practice_indicators": ("indicator",), "transparency_scenario": "chatbot"}, "candidate_prohibited"),
    ({"high_risk_path_confirmed": True, "annex_i_or_iii_category": "reviewed category A"}, "candidate_high_risk"),
    ({"high_risk_path_confirmed": True, "annex_i_or_iii_category": "reviewed category B", "operator_role": "provider"}, "candidate_high_risk"),
    ({"high_risk_path_confirmed": True, "affected_persons": ("applicants",)}, "candidate_high_risk"),
    ({"high_risk_path_confirmed": True, "gpai_role_confirmed": True}, "candidate_high_risk"),
    ({"high_risk_path_confirmed": True, "transparency_scenario": "chatbot"}, "candidate_high_risk"),
    ({"transparency_scenario": "chatbot"}, "candidate_transparency"),
    ({"transparency_scenario": "synthetic content"}, "candidate_transparency"),
    ({"transparency_scenario": "emotion recognition", "operator_role": "provider"}, "candidate_transparency"),
    ({"transparency_scenario": "deep fake", "affected_persons": ("public",)}, "candidate_transparency"),
    ({"transparency_scenario": "AI interaction", "gpai_role_confirmed": True}, "candidate_transparency"),
    ({}, "candidate_minimal"),
    ({"operator_role": "provider"}, "candidate_minimal"),
    ({"operator_role": "gpai_provider", "gpai_role_confirmed": True}, "candidate_minimal"),
    ({"affected_persons": ("staff",)}, "candidate_minimal"),
    ({"annex_i_or_iii_category": "reviewed but path not confirmed"}, "candidate_minimal"),
    ({"territorial_scope_confirmed": None}, "needs_review"),
    ({"prohibited_review_complete": None}, "needs_review"),
    ({"high_risk_path_confirmed": None}, "needs_review"),
    ({"gpai_role_confirmed": None}, "needs_review"),
    ({"transparency_review_complete": None}, "needs_review"),
]


def test_thirty_reviewer_authored_candidate_profiles() -> None:
    """Pin candidate precedence and boundary outcomes without activating them."""
    assert len(CASES) == 30
    for changes, expected in CASES:
        result = evaluate_eu_candidate(facts(**changes))
        assert result.status == expected
        assert result.source_identifier == "CELEX:32024R1689"


@given(st.sampled_from([
    "territorial_scope_confirmed", "prohibited_review_complete", "high_risk_path_confirmed",
    "gpai_role_confirmed", "transparency_review_complete",
]))
def test_missing_review_fact_never_guesses(field: str) -> None:
    """Route every unknown required review fact to needs-review."""
    result = evaluate_eu_candidate(facts(**{field: None}))
    assert result.status == "needs_review"
    assert field in result.missing_facts


def test_candidate_ruleset_has_no_production_route() -> None:
    """Keep candidate legal logic test-only until qualified approval."""
    assert all("eu-candidate" not in route.path for route in app.routes)
