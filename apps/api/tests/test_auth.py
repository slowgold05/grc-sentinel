from uuid import uuid4

from clerk_backend_api import AuthenticateRequestOptions
from clerk_backend_api.security.types import AuthStatus, RequestState
from fastapi import Request
from pydantic import SecretStr
from sqlalchemy import create_engine, text

from ruleset.auth import authenticate_tenant, clerk_options
from ruleset.config import settings


def test_clerk_options_accepts_cli_secret_without_manual_jwt_key() -> None:
    original_secret, original_jwt = settings.clerk_secret_key, settings.clerk_jwt_key
    try:
        settings.clerk_secret_key, settings.clerk_jwt_key = SecretStr("test"), None
        options = clerk_options()
        assert options.secret_key == "test"
        assert options.jwt_key is None
    finally:
        settings.clerk_secret_key, settings.clerk_jwt_key = original_secret, original_jwt


def test_verified_clerk_org_is_provisioned_and_reused() -> None:
    engine = create_engine(str(settings.database_url))
    provider_org_id = f"org_{uuid4().hex}"

    def verified(request: Request, options: AuthenticateRequestOptions) -> RequestState:
        assert options.accepts_token == ["session_token"]
        return RequestState(
            status=AuthStatus.SIGNED_IN,
            payload={"sub": "user_test", "org_id": provider_org_id, "org_name": "Auth test"},
        )

    def authenticate():
        return authenticate_tenant(
            Request({"type": "http", "headers": []}),
            engine,
            AuthenticateRequestOptions(
                secret_key="test", authorized_parties=["http://localhost:3000"], accepts_token=["session_token"]
            ),
            authenticate=verified,
        )

    try:
        identity = authenticate()
        assert authenticate().org_id == identity.org_id
        assert identity.user_id == "user_test"
    finally:
        with engine.begin() as connection:
            connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(identity.org_id)})
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": identity.org_id})
