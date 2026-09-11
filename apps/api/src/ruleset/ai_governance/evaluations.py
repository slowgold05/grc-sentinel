from collections.abc import Mapping
from uuid import UUID

from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError

from ruleset.ai_governance.models import (
    EvaluationDefinitionCreate,
    EvaluationDefinitionRecord,
    EvaluationRunCreate,
    EvaluationRunRecord,
)


class EvaluationValidationError(Exception):
    """Raised when evaluation state does not permit the requested append."""


def evaluation_result(direction: str, threshold: float, measured: float) -> str:
    """Calculate pass/fail from the approved metric direction and threshold."""
    passes = measured >= threshold if direction == "higher_is_better" else measured <= threshold
    return "pass" if passes else "fail"


def _definition(row: Mapping[str, object]) -> EvaluationDefinitionRecord:
    values = dict(row)
    values["owner"] = values.pop("owner_name")
    values.pop("org_id", None)
    values.pop("engagement_id", None)
    return EvaluationDefinitionRecord.model_validate(values)


def create_evaluation_definition(engine: Engine, org_id: UUID, system_id: UUID, actor: str, request: EvaluationDefinitionCreate) -> EvaluationDefinitionRecord:
    """Append the next version of an AI evaluation definition."""
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        system = connection.execute(text("SELECT engagement_id FROM ai_systems WHERE id = :id FOR UPDATE"), {"id": system_id}).mappings().one_or_none()
        if system is None:
            raise LookupError("AI system not found")
        version = connection.execute(text("SELECT COALESCE(max(version), 0) + 1 FROM ai_evaluation_definitions WHERE ai_system_id = :id AND name = :name"), {"id": system_id, "name": request.name}).scalar_one()
        row = connection.execute(
            text("INSERT INTO ai_evaluation_definitions (org_id, engagement_id, ai_system_id, evaluation_type, name, version, dataset_name, dataset_version, population_context, metric_name, metric_direction, threshold, owner_name, cadence, limitations, created_by) VALUES (:org_id, :engagement_id, :system_id, :evaluation_type, :name, :version, :dataset_name, :dataset_version, :population_context, :metric_name, :metric_direction, :threshold, :owner, :cadence, :limitations, :actor) RETURNING *"),
            {"org_id": org_id, "engagement_id": system["engagement_id"], "system_id": system_id, "version": version, "actor": actor, **request.model_dump(mode="json")},
        ).mappings().one()
        return _definition({**row, "threshold_approved_by": None, "latest_result": None})


def approve_evaluation_threshold(engine: Engine, org_id: UUID, definition_id: UUID, actor: str, rationale: str) -> None:
    """Append human approval for one immutable evaluation threshold."""
    try:
        with engine.begin() as connection:
            connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
            definition = connection.execute(text("SELECT engagement_id FROM ai_evaluation_definitions WHERE id = :id"), {"id": definition_id}).mappings().one_or_none()
            if definition is None:
                raise LookupError("evaluation definition not found")
            connection.execute(text("INSERT INTO ai_evaluation_threshold_approvals (org_id, engagement_id, definition_id, approved_by, rationale) VALUES (:org_id, :engagement_id, :definition_id, :actor, :rationale)"), {"org_id": org_id, "engagement_id": definition["engagement_id"], "definition_id": definition_id, "actor": actor, "rationale": rationale})
    except IntegrityError as error:
        raise EvaluationValidationError("threshold is already approved") from error


def append_evaluation_run(engine: Engine, org_id: UUID, definition_id: UUID, actor: str, request: EvaluationRunCreate) -> EvaluationRunRecord:
    """Append a run using only its definition's approved threshold."""
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        definition = connection.execute(text("SELECT d.*, a.id AS approval_id FROM ai_evaluation_definitions d LEFT JOIN ai_evaluation_threshold_approvals a ON a.definition_id = d.id WHERE d.id = :id"), {"id": definition_id}).mappings().one_or_none()
        if definition is None:
            raise LookupError("evaluation definition not found")
        if definition["approval_id"] is None:
            raise EvaluationValidationError("threshold requires human approval")
        result = evaluation_result(definition["metric_direction"], definition["threshold"], request.measured_value)
        row = connection.execute(
            text("INSERT INTO ai_evaluation_runs (org_id, engagement_id, ai_system_id, definition_id, definition_version, dataset_version, model_version, configuration_version, measured_value, result, summary, run_by) VALUES (:org_id, :engagement_id, :system_id, :definition_id, :definition_version, :dataset_version, :model_version, :configuration_version, :measured_value, :result, :summary, :actor) RETURNING *"),
            {"org_id": org_id, "engagement_id": definition["engagement_id"], "system_id": definition["ai_system_id"], "definition_id": definition_id, "definition_version": definition["version"], "dataset_version": definition["dataset_version"], "result": result, "actor": actor, **request.model_dump()},
        ).mappings().one()
        values = dict(row)
        for key in ("org_id", "engagement_id", "ai_system_id"):
            values.pop(key)
        return EvaluationRunRecord.model_validate(values)


def list_evaluation_definitions(engine: Engine, org_id: UUID, system_id: UUID) -> list[EvaluationDefinitionRecord]:
    """List definitions including approved and unmeasured state."""
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        rows = connection.execute(text("SELECT d.*, a.approved_by AS threshold_approved_by, r.result AS latest_result FROM ai_evaluation_definitions d LEFT JOIN ai_evaluation_threshold_approvals a ON a.definition_id = d.id LEFT JOIN LATERAL (SELECT result FROM ai_evaluation_runs WHERE definition_id = d.id ORDER BY tested_at DESC, id DESC LIMIT 1) r ON true WHERE d.ai_system_id = :id ORDER BY d.name, d.version DESC"), {"id": system_id}).mappings()
        return [_definition(row) for row in rows]


def list_evaluation_runs(engine: Engine, org_id: UUID, definition_id: UUID) -> list[EvaluationRunRecord]:
    """List complete append-only run history for a visible definition."""
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        rows = connection.execute(text("SELECT r.* FROM ai_evaluation_runs r JOIN ai_evaluation_definitions d ON d.id = r.definition_id WHERE r.definition_id = :id ORDER BY r.tested_at DESC, r.id DESC"), {"id": definition_id}).mappings()
        return [EvaluationRunRecord.model_validate({key: value for key, value in row.items() if key not in {"org_id", "engagement_id", "ai_system_id"}}) for row in rows]
