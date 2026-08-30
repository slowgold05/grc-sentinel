from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from ruleset.audit_hub import create_share_link, resolve_share, revoke_share
from ruleset.config import settings


def test_share_is_hashed_expiring_revocable_and_logged() -> None:
    engine = create_engine(str(settings.database_url))
    org_id, engagement_id = uuid4(), uuid4()
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        connection.execute(text("INSERT INTO orgs (id, name) VALUES (:id, 'audit test')"), {"id": org_id})
        connection.execute(
            text(
                "INSERT INTO engagements (id, org_id, company, expires_at) "
                "VALUES (:id, :org, '{\"name\":\"Example\"}', :expires)"
            ),
            {"id": engagement_id, "org": org_id, "expires": datetime.now(UTC) + timedelta(days=2)},
        )
    try:
        with pytest.raises(LookupError, match="engagement not found"):
            create_share_link(engine, org_id, uuid4(), datetime.now(UTC) + timedelta(days=1))
        token = create_share_link(engine, org_id, engagement_id, datetime.now(UTC) + timedelta(days=1))
        assert token not in str(resolve_share(engine, token))
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)}
            )
            stored_hash = connection.execute(
                text("SELECT encode(token_hash, 'hex') FROM audit_share_links")
            ).scalar_one()
            assert token not in stored_hash
            assert connection.execute(text("SELECT count(*) FROM audit_events")).scalar_one() == 1
        assert resolve_share(engine, "invalid") is None
        assert revoke_share(engine, org_id, token)
        assert resolve_share(engine, token) is None
    finally:
        with engine.begin() as connection:
            connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
