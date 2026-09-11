from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Engine, text

from ruleset.ai_governance.models import GovernanceDecisionCreate, GovernanceDecisionRecord


class DecisionValidationError(Exception):
    """Raised when a decision references invalid or incomplete tenant state."""


class StaleDecisionError(Exception):
    """Raised when the reviewer's expected decision history is no longer current."""


def create_governance_decision(
    engine: Engine, org_id: UUID, system_id: UUID, actor: str, request: GovernanceDecisionCreate
) -> GovernanceDecisionRecord:
    """Append a decision that supersedes the latest decision of the same type."""
    if request.expires_at is not None and request.expires_at <= datetime.now(UTC):
        raise DecisionValidationError("expires_at must be in the future")
    if request.decision_type == "assessment" and request.assessment_version_id is None:
        raise DecisionValidationError("assessment decision requires an assessment version")
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        engagement_id = connection.execute(
            text("SELECT engagement_id FROM ai_systems WHERE id = :id"), {"id": system_id}
        ).scalar_one_or_none()
        if engagement_id is None:
            raise LookupError("AI system not found")
        connection.execute(
            text("SELECT id FROM ai_systems WHERE id = :id FOR UPDATE"), {"id": system_id}
        ).scalar_one()
        if (
            request.assessment_version_id is not None
            and connection.execute(
                text(
                    "SELECT id FROM ai_impact_assessment_versions WHERE id = :id AND ai_system_id = :system_id"
                ),
                {"id": request.assessment_version_id, "system_id": system_id},
            ).scalar_one_or_none()
            is None
        ):
            raise DecisionValidationError("assessment version does not belong to this AI system")
        supersedes_id = connection.execute(
            text(
                "SELECT id FROM ai_governance_decisions WHERE ai_system_id = :system_id AND decision_type = :decision_type ORDER BY decided_at DESC, id DESC LIMIT 1"
            ),
            {"system_id": system_id, "decision_type": request.decision_type.value},
        ).scalar_one_or_none()
        if supersedes_id != request.expected_latest_decision_id:
            raise StaleDecisionError("decision history changed; refresh before deciding")
        row = (
            connection.execute(
                text(
                    "INSERT INTO ai_governance_decisions (org_id, engagement_id, ai_system_id, decision_type, outcome, rationale, assessment_version_id, supersedes_id, decided_by, expires_at, approval_scope, exception_owner, compensating_controls) VALUES (:org_id, :engagement_id, :system_id, :decision_type, :outcome, :rationale, :assessment_version_id, :supersedes_id, :actor, :expires_at, :approval_scope, :exception_owner, :compensating_controls) RETURNING *"
                ),
                {
                    "org_id": org_id,
                    "engagement_id": engagement_id,
                    "system_id": system_id,
                    "decision_type": request.decision_type.value,
                    "outcome": request.outcome.value,
                    "rationale": request.rationale,
                    "assessment_version_id": request.assessment_version_id,
                    "supersedes_id": supersedes_id,
                    "actor": actor,
                    "expires_at": request.expires_at,
                    "approval_scope": [item.value for item in request.approval_scope],
                    "exception_owner": request.exception_owner,
                    "compensating_controls": request.compensating_controls,
                },
            )
            .mappings()
            .one()
        )
        connection.execute(
            text(
                "INSERT INTO audit_events (org_id, engagement_id, event_type, details) VALUES (:org_id, :engagement_id, 'ai_governance_decision_created', jsonb_build_object('decision_id', CAST(:decision_id AS text), 'ai_system_id', CAST(:system_id AS text)))"
            ),
            {
                "org_id": org_id,
                "engagement_id": engagement_id,
                "decision_id": row["id"],
                "system_id": system_id,
            },
        )
        values = dict(row)
        values.pop("org_id")
        values.pop("engagement_id")
        values["expected_latest_decision_id"] = request.expected_latest_decision_id
        return GovernanceDecisionRecord.model_validate(values)


def list_governance_decisions(
    engine: Engine, org_id: UUID, system_id: UUID
) -> list[GovernanceDecisionRecord]:
    """Return complete visible decision history newest first."""
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        rows = connection.execute(
            text(
                "SELECT * FROM ai_governance_decisions WHERE ai_system_id = :id ORDER BY decided_at DESC, id DESC"
            ),
            {"id": system_id},
        ).mappings()
        return [
            GovernanceDecisionRecord.model_validate(
                {
                    **{
                        key: value
                        for key, value in row.items()
                        if key not in {"org_id", "engagement_id"}
                    },
                    "expected_latest_decision_id": row["supersedes_id"],
                }
            )
            for row in rows
        ]
