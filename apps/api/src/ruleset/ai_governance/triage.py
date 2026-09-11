import json
from importlib.resources import files
from typing import Any

from ruleset.ai_governance.models import AISystemProfile, InternalRiskRating, InternalRiskResult

_TABLE = json.loads(files("ruleset.ai_governance").joinpath("internal-risk-v1.json").read_text())


def evaluate_internal_risk(profile: AISystemProfile) -> InternalRiskResult:
    """Evaluate explicit inventory facts with the reviewed internal decision table."""
    facts = profile.model_dump(mode="json")
    missing = tuple(name for name in _TABLE["required_facts"] if facts[name] is None)
    if missing:
        return InternalRiskResult(
            ruleset_id=_TABLE["ruleset_id"], ruleset_version=_TABLE["version"],
            rating=InternalRiskRating.NEEDS_REVIEW, score=None, facts=facts,
            fired_conditions=(), missing_facts=missing,
        )

    weights: dict[str, Any] = _TABLE["weights"]
    contributions = {
        "decision_consequence": weights["decision_consequence"][facts["decision_consequence"]],
        "autonomy_level": weights["autonomy_level"][facts["autonomy_level"]],
        "human_review_coverage": weights["human_review_coverage"][facts["human_review_coverage"]],
        "sensitive_data": weights["sensitive_data"] if facts["sensitive_data"] else 0,
        "affected_persons": weights["affected_persons"] if facts["affected_persons"] else 0,
        "external_access": weights["external_access"] if facts["external_access"] else 0,
        "tool_access": weights["tool_access"] if facts["tool_access"] else 0,
    }
    score = sum(contributions.values())
    thresholds = _TABLE["thresholds"]
    rating = next(
        (InternalRiskRating(name) for name in ("low", "medium", "high") if score <= thresholds[name]),
        InternalRiskRating.CRITICAL,
    )
    fired = tuple(name for name, points in contributions.items() if points)
    return InternalRiskResult(
        ruleset_id=_TABLE["ruleset_id"], ruleset_version=_TABLE["version"], rating=rating,
        score=score, facts=facts, fired_conditions=fired, missing_facts=(),
    )
