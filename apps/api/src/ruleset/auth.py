from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from clerk_backend_api import AuthenticateRequestOptions, authenticate_request
from clerk_backend_api.security.types import AuthStatus, RequestState
from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import Engine, text

from ruleset.config import settings
from ruleset.database import engine


class TenantIdentity(BaseModel):
    org_id: UUID
    user_id: str
    provider_org_id: str


def authenticate_tenant(
    request: Request,
    engine: Engine,
    options: AuthenticateRequestOptions,
    *,
    authenticate: Callable[[Request, AuthenticateRequestOptions], RequestState] = authenticate_request,
) -> TenantIdentity:
    """Verify a Clerk session and map its active organization to an RLS tenant."""
    state = authenticate(request, options)
    payload = state.payload or {}
    provider_org_id = payload.get("org_id")
    user_id = payload.get("sub")
    if state.status != AuthStatus.SIGNED_IN or not isinstance(provider_org_id, str) or not isinstance(user_id, str):
        raise HTTPException(status_code=401, detail="signed-in organization required")
    org_name = payload.get("org_name")
    with engine.begin() as connection:
        org_id = connection.execute(
            text("SELECT provision_auth_org(:provider_org_id, :org_name)"),
            {
                "provider_org_id": provider_org_id,
                "org_name": org_name if isinstance(org_name, str) else provider_org_id,
            },
        ).scalar_one()
    return TenantIdentity(org_id=org_id, user_id=user_id, provider_org_id=provider_org_id)


def clerk_options() -> AuthenticateRequestOptions:
    if settings.clerk_secret_key is None:
        raise HTTPException(status_code=503, detail="authentication is not configured")
    return AuthenticateRequestOptions(
        secret_key=settings.clerk_secret_key.get_secret_value(),
        jwt_key=(
            settings.clerk_jwt_key.get_secret_value().replace("\\n", "\n")
            if settings.clerk_jwt_key
            else None
        ),
        authorized_parties=settings.clerk_authorized_parties,
        accepts_token=["session_token"],
    )


def require_tenant(request: Request) -> TenantIdentity:
    return authenticate_tenant(request, engine, clerk_options())


CurrentTenant = Annotated[TenantIdentity, Depends(require_tenant)]
