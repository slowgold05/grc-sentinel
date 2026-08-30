from datetime import UTC, datetime, timedelta
from uuid import uuid4

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import create_engine, text

from ruleset.config import settings
from ruleset.uploads.store import load_upload, store_upload
from ruleset.uploads.validation import validate_upload


def test_upload_round_trip_respects_rls() -> None:
    engine = create_engine(str(settings.database_url))
    org_id, other_org_id, engagement_id = uuid4(), uuid4(), uuid4()
    content = b"%PDF-1.7\nsensitive policy\n%%EOF"
    key = AESGCM.generate_key(bit_length=256)
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

    try:
        upload_id = store_upload(
            engine,
            org_id,
            engagement_id,
            validate_upload("policy.pdf", content),
            content,
            key,
        )
        assert load_upload(engine, org_id, upload_id, key) == content
        assert load_upload(engine, other_org_id, upload_id, key) is None
    finally:
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
            )
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
