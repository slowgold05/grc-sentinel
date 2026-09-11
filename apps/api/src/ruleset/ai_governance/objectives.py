from uuid import UUID

from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError

from ruleset.ai_governance.models import AIAssuranceObjective, AIAssuranceObjectiveCreate

_FRAMEWORKS = {
    "nist_ai_rmf": ("1.0", "voluntary"),
    "iso_42001": ("2023", "certifiable"),
    "singapore_model_ai_governance": ("2nd edition (2020)", "voluntary"),
}


class ObjectiveAlreadySelectedError(Exception):
    """Raised when a system already has the selected framework objective."""


def create_ai_objective(engine: Engine, org_id: UUID, system_id: UUID, selector: str, request: AIAssuranceObjectiveCreate) -> AIAssuranceObjective:
    """Select a sourced objective for one tenant-visible AI system."""
    version, objective_type = _FRAMEWORKS[request.framework]
    try:
        with engine.begin() as connection:
            connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
            engagement_id = connection.execute(text("SELECT engagement_id FROM ai_systems WHERE id = :id"), {"id": system_id}).scalar_one_or_none()
            if engagement_id is None:
                raise LookupError("AI system not found")
            row = connection.execute(
                text("INSERT INTO ai_assurance_objectives (org_id, engagement_id, ai_system_id, framework, source_version, objective_type, basis, scope, target_date, selected_by) VALUES (:org_id, :engagement_id, :system_id, :framework, :version, :type, :basis, :scope, :target_date, :selector) RETURNING *"),
                {"org_id": org_id, "engagement_id": engagement_id, "system_id": system_id, "framework": request.framework, "version": version, "type": objective_type, "basis": request.basis, "scope": request.scope, "target_date": request.target_date, "selector": selector},
            ).mappings().one()
            values = dict(row)
            values.pop("org_id")
            values.pop("engagement_id")
            return AIAssuranceObjective.model_validate(values)
    except IntegrityError as error:
        raise ObjectiveAlreadySelectedError("objective already selected") from error


def list_ai_objectives(engine: Engine, org_id: UUID, system_id: UUID) -> list[AIAssuranceObjective]:
    """List objectives for one tenant-visible AI system."""
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        rows = connection.execute(text("SELECT * FROM ai_assurance_objectives WHERE ai_system_id = :id ORDER BY created_at"), {"id": system_id}).mappings()
        return [
            AIAssuranceObjective.model_validate(
                {key: value for key, value in row.items() if key not in {"org_id", "engagement_id"}}
            )
            for row in rows
        ]
