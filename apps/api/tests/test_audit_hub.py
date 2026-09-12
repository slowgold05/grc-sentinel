from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from ruleset.audit_hub import create_share_link, get_ai_dashboard, resolve_share, revoke_share
from ruleset.config import settings


def test_share_is_hashed_expiring_revocable_and_logged() -> None:
    engine = create_engine(str(settings.database_url))
    org_id, engagement_id = uuid4(), uuid4()
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        connection.execute(
            text("INSERT INTO orgs (id, name) VALUES (:id, 'audit test')"), {"id": org_id}
        )
        connection.execute(
            text(
                "INSERT INTO engagements (id, org_id, company, expires_at) "
                'VALUES (:id, :org, \'{"name":"Example"}\', :expires)'
            ),
            {"id": engagement_id, "org": org_id, "expires": datetime.now(UTC) + timedelta(days=2)},
        )
    try:
        with pytest.raises(LookupError, match="engagement not found"):
            create_share_link(engine, org_id, uuid4(), datetime.now(UTC) + timedelta(days=1))
        token = create_share_link(
            engine, org_id, engagement_id, datetime.now(UTC) + timedelta(days=1)
        )
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
            connection.execute(
                text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)}
            )
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})


def test_ai_share_is_scoped_and_dashboard_uses_current_records() -> None:
    engine = create_engine(str(settings.database_url))
    org_id, engagement_id, system_id = uuid4(), uuid4(), uuid4()
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        connection.execute(
            text("INSERT INTO orgs (id, name) VALUES (:id, 'AI audit test')"), {"id": org_id}
        )
        connection.execute(
            text(
                "INSERT INTO engagements (id, org_id, company, expires_at) "
                'VALUES (:id, :org, \'{"name":"Fictional Fintech"}\', :expires)'
            ),
            {"id": engagement_id, "org": org_id, "expires": datetime.now(UTC) + timedelta(days=2)},
        )
        connection.execute(
            text(
                "INSERT INTO ai_systems (id, org_id, engagement_id, name, description, owner_name, "
                "business_purpose, profile, next_review_date) VALUES (:id, :org, :engagement, "
                "'Support assistant', 'Fictional', 'AI owner', 'Draft support replies', '{}', "
                "current_date - 1)"
            ),
            {"id": system_id, "org": org_id, "engagement": engagement_id},
        )
    try:
        token = create_share_link(
            engine,
            org_id,
            engagement_id,
            datetime.now(UTC) + timedelta(days=1),
            ai_system_id=system_id,
        )
        share = resolve_share(engine, token)
        assert share is not None
        assert share.ai_system["id"] == system_id
        assert share.coverage == []
        assert "not a legal determination" in share.exclusions[0]
        dashboard = get_ai_dashboard(engine, org_id)
        assert dashboard.inventory == 1
        assert dashboard.overdue_reviews == 1
        assert dashboard.governance_blockers == 1
    finally:
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)}
            )
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
