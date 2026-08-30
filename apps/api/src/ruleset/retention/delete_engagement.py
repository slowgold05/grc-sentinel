from uuid import UUID

from sqlalchemy import Engine, text


def delete_engagement(engine: Engine, org_id: UUID, engagement_id: UUID) -> bool:
    """Hard-delete one tenant engagement and all database-cascaded artifacts."""
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        deleted = connection.execute(
            text("DELETE FROM engagements WHERE id = :id RETURNING id"),
            {"id": engagement_id},
        ).scalar_one_or_none()
    return deleted is not None

