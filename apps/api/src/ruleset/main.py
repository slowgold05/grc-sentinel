from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine

from ruleset.audit_hub import AuditShare, resolve_share
from ruleset.auth import CurrentTenant, TenantIdentity
from ruleset.config import settings
from ruleset.logging import configure_logging

configure_logging()
app = FastAPI(title="Ruleset API")
engine = create_engine(str(settings.database_url), pool_pre_ping=True)


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
