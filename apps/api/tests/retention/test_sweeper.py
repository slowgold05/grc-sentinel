from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import create_engine, text

from ruleset.config import settings
from ruleset.retention.sweeper import sweep_expired


def test_sweeper_removes_only_expired_records() -> None:
    engine = create_engine(str(settings.database_url))
    org_id, expired_id, active_id, upload_id = uuid4(), uuid4(), uuid4(), uuid4()
    now = datetime.now(UTC)
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        connection.execute(text("INSERT INTO orgs (id, name) VALUES (:id, 'test')"), {"id": org_id})
        connection.execute(
            text(
                "INSERT INTO engagements (id, org_id, company, expires_at) VALUES "
                "(:expired, :org_id, '{}', :past), (:active, :org_id, '{}', :future)"
            ),
            {
                "expired": expired_id,
                "active": active_id,
                "org_id": org_id,
                "past": now - timedelta(days=1),
                "future": now + timedelta(days=1),
            },
        )
        connection.execute(
            text(
                "INSERT INTO control_evidence "
                "(org_id, test_id, status, observed, raw_response, control_ids, tested_at) "
                "VALUES (:org, 'retention-v1', 'pass', '{}', '{}', '{}', :old)"
            ),
            {"org": org_id, "old": now - timedelta(days=366)},
        )
        connection.execute(
            text(
                "INSERT INTO audit_events (org_id, engagement_id, event_type, created_at) "
                "VALUES (:org, :engagement, 'retention_test', :old)"
            ),
            {"org": org_id, "engagement": active_id, "old": now - timedelta(days=366)},
        )
        connection.execute(
            text(
                "INSERT INTO audit_share_links "
                "(org_id, engagement_id, token_hash, expires_at) "
                "VALUES (:org, :engagement, :hash, :past)"
            ),
            {"org": org_id, "engagement": active_id, "hash": b"expired", "past": now - timedelta(days=1)},
        )
        connection.execute(
            text(
                "INSERT INTO osint_cache (org_id, domain, module, result, expires_at) "
                "VALUES (:org_id, 'example.com', 'headers', '{}', :past)"
            ),
            {"org_id": org_id, "past": now - timedelta(days=1)},
        )
        connection.execute(
            text(
                "INSERT INTO uploads (id, org_id, engagement_id, filename, media_type, sha256, "
                "ciphertext, nonce, wrapped_key, key_nonce, expires_at) VALUES (:id, :org_id, "
                ":engagement_id, 'test.pdf', 'application/pdf', :sha, '', '', '', '', :past)"
            ),
            {
                "id": upload_id,
                "org_id": org_id,
                "engagement_id": active_id,
                "sha": "2" * 64,
                "past": now - timedelta(days=1),
            },
        )

    try:
        result = sweep_expired(engine, now)
        assert result.expired_uploads >= 1
        assert result.expired_engagements >= 1
        assert result.expired_osint >= 1
        assert result.expired_evidence >= 1
        assert result.expired_audit_events >= 1
        assert result.expired_share_links >= 1
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
            )
            assert connection.execute(
                text("SELECT id FROM engagements WHERE id = :id"), {"id": active_id}
            ).scalar_one() == active_id
    finally:
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
            )
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
