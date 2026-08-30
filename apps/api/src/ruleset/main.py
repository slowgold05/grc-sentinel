from uuid import UUID
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from ruleset.audit_hub import AuditShare, resolve_share
from ruleset.auth import CurrentTenant, TenantIdentity
from ruleset.config import settings
from ruleset.coverage_store import CoverageRow, list_coverage_results
from ruleset.database import engine
from ruleset.document_ingestion import IngestedDocument, ingest_document
from ruleset.engagements import (
    EngagementCreate,
    EngagementCreated,
    EngagementSummary,
    create_engagement,
    list_engagements,
)
from ruleset.logging import configure_logging
from ruleset.monitoring.connections import (
    AwsCredentials,
    GitHubCredentials,
    delete_connection,
    save_connection,
)
from ruleset.monitoring.runner import EvidenceRun, run_aws_checks, run_github_checks
from ruleset.osint.snapshot import SecurityPostureSnapshot
from ruleset.posture_service import collect_posture
from ruleset.risk_register import (
    Risk,
    RiskCreate,
    RiskStatusUpdate,
    create_risk,
    delete_risk,
    list_risks,
    update_risk_status,
)
from ruleset.retention.delete_engagement import delete_engagement
from ruleset.errors import DocumentParseError, InvalidUploadError
from ruleset.uploads.crypto import decode_master_key
from ruleset.uploads.validation import MAX_UPLOAD_BYTES

configure_logging()
app = FastAPI(title="Ruleset API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.clerk_authorized_parties,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Filename"],
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


@app.post("/api/connections", status_code=status.HTTP_201_CREATED)
def post_connection(
    payload: GitHubCredentials | AwsCredentials, identity: CurrentTenant
) -> dict[str, str | UUID]:
    """Store tenant-bound encrypted read-only connector credentials."""
    if settings.upload_master_key_base64 is None:
        raise HTTPException(status_code=503, detail="credential encryption is not configured")
    connection_id = save_connection(
        engine,
        identity.org_id,
        payload,
        decode_master_key(settings.upload_master_key_base64.get_secret_value()),
    )
    return {"id": connection_id, "provider": payload.provider}


@app.delete("/api/connections/{provider}", status_code=status.HTTP_204_NO_CONTENT)
def remove_connection(
    provider: Literal["github", "aws"], identity: CurrentTenant
) -> Response:
    if not delete_connection(engine, identity.org_id, provider):
        raise HTTPException(status_code=404, detail="connection not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/api/connections/github/run", response_model=list[EvidenceRun])
async def post_github_run(identity: CurrentTenant) -> list[EvidenceRun]:
    """Run read-only GitHub checks and persist immutable evidence."""
    if settings.upload_master_key_base64 is None:
        raise HTTPException(status_code=503, detail="credential encryption is not configured")
    try:
        return await run_in_threadpool(
            run_github_checks,
            engine,
            identity.org_id,
            decode_master_key(settings.upload_master_key_base64.get_secret_value()),
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/api/connections/aws/run", response_model=list[EvidenceRun])
async def post_aws_run(identity: CurrentTenant) -> list[EvidenceRun]:
    """Assume the configured read-only AWS role and persist test evidence."""
    if settings.upload_master_key_base64 is None:
        raise HTTPException(status_code=503, detail="credential encryption is not configured")
    try:
        return await run_in_threadpool(
            run_aws_checks,
            engine,
            identity.org_id,
            decode_master_key(settings.upload_master_key_base64.get_secret_value()),
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post(
    "/api/engagements",
    response_model=EngagementCreated,
    status_code=status.HTTP_201_CREATED,
)
def post_engagement(payload: EngagementCreate, identity: CurrentTenant) -> EngagementCreated:
    return create_engagement(engine, identity.org_id, payload)


@app.get("/api/engagements", response_model=list[EngagementSummary])
def get_engagements(identity: CurrentTenant) -> list[EngagementSummary]:
    return list_engagements(engine, identity.org_id)


@app.get("/api/engagements/{engagement_id}/coverage", response_model=list[CoverageRow])
def get_coverage(engagement_id: UUID, identity: CurrentTenant) -> list[CoverageRow]:
    return list_coverage_results(engine, identity.org_id, engagement_id)


@app.delete("/api/engagements/{engagement_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_engagement(engagement_id: UUID, identity: CurrentTenant) -> Response:
    if not delete_engagement(engine, identity.org_id, engagement_id):
        raise HTTPException(status_code=404, detail="engagement not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get(
    "/api/engagements/{engagement_id}/posture",
    response_model=SecurityPostureSnapshot,
)
async def get_posture(
    engagement_id: UUID, identity: CurrentTenant
) -> SecurityPostureSnapshot:
    try:
        return await run_in_threadpool(collect_posture, engine, identity.org_id, engagement_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post(
    "/api/engagements/{engagement_id}/uploads",
    response_model=IngestedDocument,
    status_code=status.HTTP_201_CREATED,
)
async def post_upload(
    engagement_id: UUID,
    request: Request,
    identity: CurrentTenant,
    x_filename: str = Header(min_length=1, max_length=255),
) -> IngestedDocument:
    if settings.upload_master_key_base64 is None:
        raise HTTPException(status_code=503, detail="upload encryption is not configured")
    content = bytearray()
    async for chunk in request.stream():
        content.extend(chunk)
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="upload exceeds 20 MiB")
    try:
        return await run_in_threadpool(
            ingest_document,
            engine,
            identity.org_id,
            engagement_id,
            x_filename,
            bytes(content),
            decode_master_key(settings.upload_master_key_base64.get_secret_value()),
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (InvalidUploadError, DocumentParseError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


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
