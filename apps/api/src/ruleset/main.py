from uuid import UUID

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware

from ruleset.audit_hub import AuditShare, resolve_share
from ruleset.auth import CurrentTenant, TenantIdentity
from ruleset.config import settings
from ruleset.database import engine
from ruleset.engagements import EngagementCreate, EngagementCreated, create_engagement
from ruleset.logging import configure_logging
from ruleset.risk_register import (
    Risk,
    RiskCreate,
    RiskStatusUpdate,
    create_risk,
    delete_risk,
    list_risks,
    update_risk_status,
)

configure_logging()
app = FastAPI(title="Ruleset API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.clerk_authorized_parties,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the API process is available."""
    return {"status": "ok"}


@app.get("/audit/share/{token}", response_model=AuditShare)
def open_audit_share(token: str) -> AuditShare:
    """Resolve an unguessable, unexpired read-only audit share."""
    share = resolve_share(engine, token)
    if share is None:
        raise HTTPException(status_code=404, detail="share not found or expired")
    return share


@app.get("/api/tenant", response_model=TenantIdentity)
def current_tenant(identity: CurrentTenant) -> TenantIdentity:
    """Prove the verified Clerk organization-to-RLS tenant mapping."""
    return identity


@app.post(
    "/api/engagements",
    response_model=EngagementCreated,
    status_code=status.HTTP_201_CREATED,
)
def post_engagement(payload: EngagementCreate, identity: CurrentTenant) -> EngagementCreated:
    return create_engagement(engine, identity.org_id, payload)


@app.get("/api/risks", response_model=list[Risk])
def get_risks(identity: CurrentTenant) -> list[Risk]:
    return list_risks(engine, identity.org_id)


@app.post("/api/risks", status_code=status.HTTP_201_CREATED)
def post_risk(payload: RiskCreate, identity: CurrentTenant) -> dict[str, UUID]:
    return {"id": create_risk(engine, identity.org_id, **payload.model_dump())}


@app.patch("/api/risks/{risk_id}/status", status_code=status.HTTP_204_NO_CONTENT)
def patch_risk_status(
    risk_id: UUID, payload: RiskStatusUpdate, identity: CurrentTenant
) -> Response:
    if not update_risk_status(engine, identity.org_id, risk_id, payload.status):
        raise HTTPException(status_code=404, detail="risk not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.delete("/api/risks/{risk_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_risk(risk_id: UUID, identity: CurrentTenant) -> Response:
    if not delete_risk(engine, identity.org_id, risk_id):
        raise HTTPException(status_code=404, detail="risk not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
