from ruleset.ai_governance.models import DeploymentGateFacts, DeploymentGateResult


def evaluate_deployment_gate(facts: DeploymentGateFacts) -> DeploymentGateResult:
    """Return every deployment blocker from explicit, current governance facts."""
    blockers = []
    if not facts.assessment_current:
        blockers.append("current_assessment_missing")
    elif not facts.assessment_approved:
        blockers.append("current_assessment_not_approved")
    if not facts.residual_risk_decided:
        blockers.append("residual_risk_decision_missing")
    elif not facts.residual_risk_accepted:
        blockers.append("residual_risk_not_accepted")
    if facts.evaluation_required and not facts.evaluation_current:
        blockers.append("current_evaluation_missing")
    elif facts.evaluation_required and not facts.evaluation_passed:
        blockers.append("required_evaluation_failed")
    if facts.exception_required and (
        facts.exception_expires_at is None or facts.exception_expires_at <= facts.evaluated_at
    ):
        blockers.append("valid_exception_missing")
    if facts.legal_review_required and not facts.legal_review_approved:
        blockers.append("legal_review_not_approved")
    return DeploymentGateResult(allowed=not blockers, blockers=tuple(blockers))
