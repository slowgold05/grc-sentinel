import json
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, SecretStr
from sqlalchemy import Engine, text

from ruleset.uploads.crypto import EncryptedBlob, decrypt_upload, encrypt_upload


class GitHubCredentials(BaseModel):
    provider: Literal["github"]
    organization: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9-]{0,38}$")
    token: SecretStr
    scopes: list[str] = Field(default_factory=list)


class AwsCredentials(BaseModel):
    provider: Literal["aws"]
    role_arn: str = Field(pattern=r"^arn:aws:iam::[0-9]{12}:role/.+$")
    external_id: SecretStr
    region: str = Field(pattern=r"^[a-z]{2}-[a-z]+-[0-9]$")
    scopes: list[str] = Field(default_factory=list)


Credentials = GitHubCredentials | AwsCredentials


def save_connection(
    engine: Engine, org_id: UUID, credentials: Credentials, master_key: bytes
) -> UUID:
    """Encrypt and upsert one provider connection for a tenant."""
    payload = credentials.model_dump(mode="json")
    payload.update(
        {name: value.get_secret_value() for name, value in credentials.__dict__.items() if isinstance(value, SecretStr)}
    )
    blob = encrypt_upload(json.dumps(payload).encode(), org_id, master_key)
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        return connection.execute(
            text(
                "INSERT INTO monitoring_connections "
                "(org_id, provider, ciphertext, nonce, wrapped_key, key_nonce, scopes) VALUES "
                "(:org_id, :provider, :ciphertext, :nonce, :wrapped_key, :key_nonce, :scopes) "
                "ON CONFLICT (org_id, provider) DO UPDATE SET ciphertext = EXCLUDED.ciphertext, "
                "nonce = EXCLUDED.nonce, wrapped_key = EXCLUDED.wrapped_key, "
                "key_nonce = EXCLUDED.key_nonce, scopes = EXCLUDED.scopes RETURNING id"
            ),
            {"org_id": org_id, "provider": credentials.provider, "scopes": credentials.scopes, **blob.model_dump()},
        ).scalar_one()


def load_connection(
    engine: Engine, org_id: UUID, provider: Literal["github", "aws"], master_key: bytes
) -> Credentials | None:
    """Decrypt a tenant connection for an execution worker."""
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        row = connection.execute(
            text("SELECT ciphertext, nonce, wrapped_key, key_nonce FROM monitoring_connections WHERE provider = :provider"),
            {"provider": provider},
        ).mappings().one_or_none()
    if row is None:
        return None
    payload = json.loads(decrypt_upload(EncryptedBlob.model_validate(row), org_id, master_key))
    return GitHubCredentials.model_validate(payload) if provider == "github" else AwsCredentials.model_validate(payload)


def delete_connection(engine: Engine, org_id: UUID, provider: str) -> bool:
    """Hard-delete one tenant provider connection."""
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        return bool(connection.execute(text("DELETE FROM monitoring_connections WHERE provider = :provider"), {"provider": provider}).rowcount)
