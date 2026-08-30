from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import create_engine, text

from ruleset.config import settings
from ruleset.rules.models import Determination
from ruleset.rules.store import store_determinations


def test_stores_determination_once() -> None:
    engine = create_engine(str(settings.database_url))
    org_id, engagement_id = uuid4(), uuid4()
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        connection.execute(
            text("INSERT INTO orgs (id, name) VALUES (:id, 'test')"), {"id": org_id}
        )
        connection.execute(
            text(
                "INSERT INTO engagements (id, org_id, company, expires_at) "
                "VALUES (:id, :org_id, '{}', :expires_at)"
            ),
            {
                "id": engagement_id,
                "org_id": org_id,
                "expires_at": datetime.now(UTC) + timedelta(days=1),
            },
        )
    determination = Determination(
        rule_id="hipaa-covered-entity-v2",
        rule_version=2,
        regulation="HIPAA",
        explanation="Handles PHI for US persons",
        citations=["45 CFR §164.302"],
        facts={"data_types": ["phi"], "geos": ["us"]},
    )

    try:
        assert store_determinations(engine, org_id, engagement_id, [determination]) == 1
        assert store_determinations(engine, org_id, engagement_id, [determination]) == 0
    finally:
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
            )
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
