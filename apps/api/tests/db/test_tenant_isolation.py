from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection

from ruleset.config import settings


def _set_org(connection: Connection, org_id: object) -> None:
    connection.execute(text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)})


def test_org_cannot_read_another_orgs_engagement() -> None:
    engine = create_engine(str(settings.database_url))
    org_a, org_b = uuid4(), uuid4()
    engagement_a, engagement_b = uuid4(), uuid4()
    expires = datetime.now(UTC) + timedelta(days=1)

    for org_id, engagement_id in ((org_a, engagement_a), (org_b, engagement_b)):
        with engine.begin() as connection:
            _set_org(connection, org_id)
            connection.execute(
                text("INSERT INTO orgs (id, name) VALUES (:id, :name)"),
                {"id": org_id, "name": str(org_id)},
            )
            connection.execute(
                text(
                    "INSERT INTO engagements (id, org_id, company, expires_at) "
                    "VALUES (:id, :org_id, '{}', :expires_at)"
                ),
                {"id": engagement_id, "org_id": org_id, "expires_at": expires},
            )

    try:
        with engine.begin() as connection:
            _set_org(connection, org_a)
            visible = list(connection.execute(text("SELECT id FROM engagements")).scalars())
        assert visible == [engagement_a]
    finally:
        for org_id in (org_a, org_b):
            with engine.begin() as connection:
                _set_org(connection, org_id)
                connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
