from os import urandom
from uuid import uuid4

from sqlalchemy import create_engine, text

from ruleset.config import settings
from ruleset.monitoring.connections import (
    GitHubCredentials,
    delete_connection,
    load_connection,
    save_connection,
)


def test_connection_credentials_are_encrypted_and_tenant_scoped() -> None:
    engine = create_engine(str(settings.database_url))
    org_id, master_key = uuid4(), urandom(32)
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        connection.execute(
            text("INSERT INTO orgs (id, name) VALUES (:id, 'connection test')"), {"id": org_id}
        )
    credentials = GitHubCredentials(
        provider="github", organization="ruleset-demo", token="secret-token"
    )
    try:
        save_connection(engine, org_id, credentials, master_key)
        loaded = load_connection(engine, org_id, "github", master_key)
        assert isinstance(loaded, GitHubCredentials)
        assert loaded.token.get_secret_value() == "secret-token"
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)}
            )
            ciphertext = connection.execute(
                text("SELECT ciphertext FROM monitoring_connections")
            ).scalar_one()
        assert b"secret-token" not in ciphertext
        assert delete_connection(engine, org_id, "github")
    finally:
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)}
            )
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
