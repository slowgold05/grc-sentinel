import json
from pathlib import Path

from ruleset.rules.engine import evaluate_scope
from ruleset.rules.models import CompanyFacts, Rule


FIXTURES = Path(__file__).parent


def test_glba_candidate_set_covers_review_boundaries() -> None:
    """Keep the non-active GLBA reviewer package deterministic and complete."""
    rule = Rule.model_validate_json((FIXTURES / "glba-candidate-rule.json").read_text())
    profiles = json.loads((FIXTURES / "glba-golden-candidates.json").read_text())

    assert len(profiles) >= 30
    assert {profile["expected_status"] for profile in profiles} == {
        "applicable",
        "not_applicable",
        "needs_review",
    }
    for profile in profiles:
        result = evaluate_scope(CompanyFacts(profile["facts"]), [rule])[0]
        assert result.status == profile["expected_status"], profile["case_id"]
