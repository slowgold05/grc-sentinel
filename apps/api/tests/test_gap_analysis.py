from datetime import UTC, datetime, timedelta
import json
from uuid import uuid4

from sqlalchemy import create_engine, text

from ruleset.config import settings
from ruleset.gap_analysis import find_coverage_candidates


def test_finds_best_matching_section() -> None:
    engine = create_engine(str(settings.database_url))
    framework_id, control_id = uuid4(), uuid4()
    org_id, engagement_id, upload_id, chunk_id = uuid4(), uuid4(), uuid4(), uuid4()
    vector = json.dumps([1.0, *([0.0] * 1023)])
    expires = datetime.now(UTC) + timedelta(days=1)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO frameworks (id, name, version, publisher, machine_readable_source) "
                "VALUES (:id, :name, '1', 'test', 'test')"
            ),
            {"id": framework_id, "name": f"test-{framework_id}"},
        )
        connection.execute(
            text(
                "INSERT INTO controls (id, framework_id, control_code, title, description) "
                "VALUES (:id, :framework_id, 'T-1', 'Test', 'Test')"
            ),
            {"id": control_id, "framework_id": framework_id},
        )
        connection.execute(
            text(
                "INSERT INTO control_embeddings (control_id, embedding, chunk_text) "
                "VALUES (:id, CAST(:vector AS vector), 'Test')"
            ),
            {"id": control_id, "vector": vector},
        )
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        connection.execute(text("INSERT INTO orgs (id, name) VALUES (:id, 'test')"), {"id": org_id})
        connection.execute(
            text(
                "INSERT INTO engagements (id, org_id, company, expires_at) "
                "VALUES (:id, :org_id, '{}', :expires)"
            ),
            {"id": engagement_id, "org_id": org_id, "expires": expires},
        )
        connection.execute(
            text(
                "INSERT INTO uploads (id, org_id, engagement_id, filename, media_type, sha256, "
                "ciphertext, nonce, wrapped_key, key_nonce, expires_at) VALUES (:id, :org_id, "
                ":engagement_id, 'test.pdf', 'application/pdf', :sha, '', '', '', '', :expires)"
            ),
            {
                "id": upload_id,
                "org_id": org_id,
                "engagement_id": engagement_id,
                "sha": "1" * 64,
                "expires": expires,
            },
        )
        connection.execute(
            text(
                "INSERT INTO upload_chunks (id, org_id, upload_id, seq, text, embedding) "
                "VALUES (:id, :org_id, :upload_id, 1, 'Test', CAST(:vector AS vector))"
            ),
            {"id": chunk_id, "org_id": org_id, "upload_id": upload_id, "vector": vector},
        )

    try:
        match = find_coverage_candidates(engine, org_id, upload_id, [control_id])[0]
        assert (match.chunk_id, match.similarity, match.status) == (chunk_id, 1.0, "candidate")
        assert (match.control_text, match.document_text) == ("Test: Test", "Test")
    finally:
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
            )
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
            connection.execute(text("DELETE FROM frameworks WHERE id = :id"), {"id": framework_id})
