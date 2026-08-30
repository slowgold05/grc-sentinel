from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import Engine, text

from ruleset.uploads.crypto import EncryptedBlob, decrypt_upload, encrypt_upload
from ruleset.uploads.validation import UploadMetadata


def store_upload(
    engine: Engine,
    org_id: UUID,
    engagement_id: UUID,
    metadata: UploadMetadata,
    content: bytes,
    master_key: bytes,
) -> UUID:
    """Encrypt and store a validated upload for 90 days."""
    blob = encrypt_upload(content, org_id, master_key)
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        return connection.execute(
            text(
                "INSERT INTO uploads "
                "(org_id, engagement_id, filename, media_type, sha256, ciphertext, nonce, "
                "wrapped_key, key_nonce, expires_at) VALUES (:org_id, :engagement_id, "
                ":filename, :media_type, :sha256, :ciphertext, :nonce, :wrapped_key, "
                ":key_nonce, :expires_at) RETURNING id"
            ),
            {
                "org_id": org_id,
                "engagement_id": engagement_id,
                **metadata.model_dump(),
                **blob.model_dump(),
                "expires_at": datetime.now(UTC) + timedelta(days=90),
            },
        ).scalar_one()


def load_upload(engine: Engine, org_id: UUID, upload_id: UUID, master_key: bytes) -> bytes | None:
    """Load and decrypt an upload visible to the current tenant."""
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        row = connection.execute(
            text(
                "SELECT ciphertext, nonce, wrapped_key, key_nonce FROM uploads WHERE id = :id"
            ),
            {"id": upload_id},
        ).mappings().one_or_none()
    return None if row is None else decrypt_upload(EncryptedBlob.model_validate(row), org_id, master_key)

