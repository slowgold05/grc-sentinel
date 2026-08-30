from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import create_engine, text

from ruleset.config import settings
from ruleset.coverage_store import store_coverage_results
from ruleset.coverage_verifier import CoverageClaim, verify_evidence_quote


def test_stores_only_verified_coverage_results() -> None:
    engine = create_engine(str(settings.database_url))
    org_id, engagement_id, upload_id = uuid4(), uuid4(), uuid4()
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        connection.execute(text("INSERT INTO orgs (id, name) VALUES (:id, 'coverage test')"), {"id": org_id})
        connection.execute(
            text("INSERT INTO engagements (id, org_id, company, expires_at) VALUES (:id, :org, '{}', :expires)"),
            {"id": engagement_id, "org": org_id, "expires": datetime.now(UTC) + timedelta(days=1)},
        )
        connection.execute(
            text(
                "INSERT INTO uploads (id, org_id, engagement_id, filename, media_type, sha256, "
                "ciphertext, nonce, wrapped_key, key_nonce, expires_at) VALUES "
                "(:id, :org, :engagement, 'p.pdf', 'application/pdf', :sha, :blob, :blob, "
                ":blob, :blob, :expires)"
            ),
            {
                "id": upload_id,
                "org": org_id,
                "engagement": engagement_id,
                "sha": "0" * 64,
                "blob": b"x",
                "expires": datetime.now(UTC) + timedelta(days=1),
            },
        )
        control_id = connection.execute(text("SELECT id FROM controls LIMIT 1")).scalar_one()
    claim = CoverageClaim(control_id=control_id, chunk_id=None, status="missing", evidence_quote="", gap="Add control.")
    result = verify_evidence_quote(claim, None)
    try:
        assert store_coverage_results(engine, org_id, engagement_id, upload_id, [result]) == 1
    finally:
        with engine.begin() as connection:
            connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
