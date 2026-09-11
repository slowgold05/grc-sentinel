import json
from importlib.resources import files

from ruleset.ai_governance.models import (
    CandidateLegalStatus,
    EUCandidateFacts,
    EUCandidateResult,
)

_TABLE = json.loads(files("ruleset.ai_governance").joinpath("eu-candidate-v1.json").read_text())


def evaluate_eu_candidate(facts: EUCandidateFacts) -> EUCandidateResult:
    """Route explicit reviewer facts through the test-only candidate branches."""
    required = (
        "territorial_scope_confirmed", "prohibited_review_complete",
        "high_risk_path_confirmed", "gpai_role_confirmed", "transparency_review_complete",
    )
    missing = tuple(name for name in required if getattr(facts, name) is None)
    if missing:
        status, fired = CandidateLegalStatus.NEEDS_REVIEW, None
    elif not facts.territorial_scope_confirmed:
        status, fired = CandidateLegalStatus.NOT_APPLICABLE, "territorial_scope_not_confirmed"
    elif facts.prohibited_practice_indicators:
        status, fired = CandidateLegalStatus.PROHIBITED, "reviewer_flagged_prohibited_indicator"
    elif facts.high_risk_path_confirmed:
        status, fired = CandidateLegalStatus.HIGH_RISK, "reviewer_confirmed_high_risk_path"
    elif facts.transparency_scenario:
        status, fired = CandidateLegalStatus.TRANSPARENCY, "reviewer_confirmed_transparency_scenario"
    else:
        status, fired = CandidateLegalStatus.MINIMAL, "no_candidate_branch_confirmed"
    return EUCandidateResult(
        ruleset_id=_TABLE["ruleset_id"], ruleset_version=_TABLE["version"],
        source_identifier=_TABLE["source_identifier"], status=status,
        fired_condition=fired, missing_facts=missing,
    )
