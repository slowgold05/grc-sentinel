from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import create_engine, text

from ruleset.config import settings
from ruleset.uploads.chunks import store_sections
from ruleset.uploads.embed_chunks import embed_sections
from ruleset.uploads.parse_worker import DocumentSection, ParsedDocument


def test_stores_only_non_empty_sections() -> None:
    engine = create_engine(str(settings.database_url))
    org_id, engagement_id, upload_id = uuid4(), uuid4(), uuid4()
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        connection.execute(text("INSERT INTO orgs (id, name) VALUES (:id, 'test')"), {"id": org_id})
        connection.execute(
            text(
                "INSERT INTO engagements (id, org_id, company, expires_at) "
                "VALUES (:id, :org_id, '{}', :expires_at)"
            ),
            {"id": engagement_id, "org_id": org_id, "expires_at": datetime.now(UTC) + timedelta(days=1)},
        )
        connection.execute(
            text(
                "INSERT INTO uploads (id, org_id, engagement_id, filename, media_type, sha256, "
                "ciphertext, nonce, wrapped_key, key_nonce, expires_at) VALUES (:id, :org_id, "
                ":engagement_id, 'test.pdf', 'application/pdf', :sha, '', '', '', '', :expires_at)"
            ),
            {"id": upload_id, "org_id": org_id, "engagement_id": engagement_id, "sha": "0" * 64, "expires_at": datetime.now(UTC) + timedelta(days=1)},
        )
    document = ParsedDocument(
        sections=[DocumentSection(seq=1, text="Access control"), DocumentSection(seq=2, text=" ")]
    )

    try:
        assert store_sections(engine, org_id, upload_id, document) == 1
        assert embed_sections(
            engine,
            org_id,
            upload_id,
            lambda texts: [[0.0] * 1024 for _ in texts],
        ) == 1
        assert embed_sections(engine, org_id, upload_id, lambda texts: []) == 0
    finally:
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
            )
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
