from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import Engine, text

from ruleset.ai_governance.models import AIChangeType, AISystemVersionCreate, AISystemVersionRecord


def approval_is_current(approval_scope: Iterable[AIChangeType], later_changes: Iterable[AIChangeType]) -> bool:
    """Keep an approval current only when no later change intersects its scope."""
    return set(approval_scope).isdisjoint(later_changes)


def append_system_version(engine: Engine, org_id: UUID, system_id: UUID, actor: str, request: AISystemVersionCreate) -> AISystemVersionRecord:
    """Append an exact AI system configuration version."""
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        system = connection.execute(text("SELECT engagement_id FROM ai_systems WHERE id = :id FOR UPDATE"), {"id": system_id}).mappings().one_or_none()
        if system is None:
            raise LookupError("AI system not found")
        version = connection.execute(text("SELECT COALESCE(max(version), 0) + 1 FROM ai_system_versions WHERE ai_system_id = :id"), {"id": system_id}).scalar_one()
        row = connection.execute(
            text("INSERT INTO ai_system_versions (org_id, engagement_id, ai_system_id, version, model_version, prompt_version, corpus_version, tool_permissions_version, purpose_version, vendor_terms_version, material_changes, created_by) VALUES (:org_id, :engagement_id, :system_id, :version, :model_version, :prompt_version, :corpus_version, :tool_permissions_version, :purpose_version, :vendor_terms_version, :material_changes, :actor) RETURNING *"),
            {"org_id": org_id, "engagement_id": system["engagement_id"], "system_id": system_id, "version": version, "actor": actor, **request.model_dump(mode="json")},
        ).mappings().one()
        values = dict(row)
        values.pop("org_id")
        values.pop("engagement_id")
        values["review_required"] = bool(row["material_changes"])
        return AISystemVersionRecord.model_validate(values)


def list_system_versions(engine: Engine, org_id: UUID, system_id: UUID) -> list[AISystemVersionRecord]:
    """Return complete AI system configuration history."""
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        rows = connection.execute(text("SELECT * FROM ai_system_versions WHERE ai_system_id = :id ORDER BY version DESC"), {"id": system_id}).mappings()
        return [AISystemVersionRecord.model_validate({**{key: value for key, value in row.items() if key not in {"org_id", "engagement_id"}}, "review_required": bool(row["material_changes"])}) for row in rows]
