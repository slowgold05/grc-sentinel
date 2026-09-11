import json
from collections.abc import Mapping
from uuid import UUID

from sqlalchemy import Engine, text

from ruleset.ai_governance.models import AISystemCreate, AISystemRecord, LifecycleStatus


def _set_org(connection: object, org_id: UUID) -> None:
    connection.execute(
        text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
    )


def _record(row: Mapping[str, object]) -> AISystemRecord:
    values = dict(row)
    values["owner"] = values.pop("owner_name")
    values.pop("org_id")
    return AISystemRecord.model_validate(values)


def create_ai_system(
    engine: Engine, org_id: UUID, actor: str, request: AISystemCreate
) -> AISystemRecord:
    """Create one tenant-bound inventory record and its audit event."""
    with engine.begin() as connection:
        _set_org(connection, org_id)
        engagement_id = request.engagement_id
        if connection.execute(
            text("SELECT id FROM engagements WHERE id = :id"), {"id": engagement_id}
        ).scalar_one_or_none() is None:
            raise LookupError("engagement not found")
        row = connection.execute(
            text(
                "INSERT INTO ai_systems (org_id, engagement_id, name, description, owner_name, "
                "business_purpose, profile, deployment_date, next_review_date) VALUES "
                "(:org_id, :engagement_id, :name, :description, :owner, :business_purpose, "
                "CAST(:profile AS jsonb), :deployment_date, :next_review_date) RETURNING *"
            ),
            {
                "org_id": org_id,
                "engagement_id": engagement_id,
                "name": request.name,
                "description": request.description,
                "owner": request.owner,
                "business_purpose": request.business_purpose,
                "profile": json.dumps(request.profile.model_dump(mode="json")),
                "deployment_date": request.deployment_date,
                "next_review_date": request.next_review_date,
            },
        ).mappings().one()
        connection.execute(
            text(
                "INSERT INTO audit_events (org_id, engagement_id, event_type, details) VALUES "
                "(:org_id, :engagement_id, 'ai_system_created', CAST(:details AS jsonb))"
            ),
            {
                "org_id": org_id,
                "engagement_id": engagement_id,
                "details": json.dumps({"ai_system_id": str(row["id"]), "actor": actor}),
            },
        )
        return _record(row)


def list_ai_systems(engine: Engine, org_id: UUID) -> list[AISystemRecord]:
    """List AI systems visible to the active database tenant."""
    with engine.begin() as connection:
        _set_org(connection, org_id)
        rows = connection.execute(text("SELECT * FROM ai_systems ORDER BY created_at DESC")).mappings()
        return [_record(row) for row in rows]


def get_ai_system(engine: Engine, org_id: UUID, system_id: UUID) -> AISystemRecord | None:
    """Return one tenant-visible AI system."""
    with engine.begin() as connection:
        _set_org(connection, org_id)
        row = connection.execute(
            text("SELECT * FROM ai_systems WHERE id = :id"), {"id": system_id}
        ).mappings().one_or_none()
        return _record(row) if row else None


def update_ai_system_state(
    engine: Engine, org_id: UUID, system_id: UUID, status: LifecycleStatus, actor: str
) -> AISystemRecord | None:
    """Change lifecycle state while protected approval gates are unavailable."""
    if status in {LifecycleStatus.APPROVED, LifecycleStatus.DEPLOYED}:
        raise ValueError("approval gate is required for this lifecycle state")
    with engine.begin() as connection:
        _set_org(connection, org_id)
        row = connection.execute(
            text(
                "UPDATE ai_systems SET status = :status, updated_at = now() WHERE id = :id "
                "RETURNING *"
            ),
            {"status": status.value, "id": system_id},
        ).mappings().one_or_none()
        if row is None:
            return None
        connection.execute(
            text(
                "INSERT INTO audit_events (org_id, engagement_id, event_type, details) VALUES "
                "(:org_id, :engagement_id, 'ai_system_state_changed', CAST(:details AS jsonb))"
            ),
            {
                "org_id": org_id,
                "engagement_id": row["engagement_id"],
                "details": json.dumps(
                    {"ai_system_id": str(system_id), "actor": actor, "status": status.value}
                ),
            },
        )
        return _record(row)
