from datetime import UTC, datetime, timedelta
from functools import partial
from uuid import UUID
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from ruleset.audit_hub import (
    AuditShare,
    AuditShareCreate,
    AuditShareCreated,
    create_share_link,
    resolve_share,
    revoke_share,
)
from ruleset.auth import CurrentTenant, TenantIdentity
from ruleset.config import settings
from ruleset.coverage_analysis import analyze_upload_coverage
from ruleset.coverage_store import CoverageRow, list_coverage_results
from ruleset.database import engine
from ruleset.document_ingestion import IngestedDocument, ingest_document
from ruleset.engagements import (
    AssuranceReadiness,
    EngagementCreate,
    EngagementCreated,
    EngagementSummary,
    create_engagement,
    get_assurance_readiness,
    list_engagements,
)
from ruleset.generation.store import (
    PolicySummary,
    UsageSummary,
    export_stored_policy,
    list_policies,
    summarize_usage,
)
from ruleset.generation.openai_compatible_client import call_model_json
from ruleset.framework_drift import (
    FrameworkImpact,
    FrameworkOption,
    framework_impact,
    list_frameworks,
)
from ruleset.logging import configure_logging
from ruleset.kb.embed_controls import ollama_embed
from ruleset.monitoring.connections import (
    AwsCredentials,
    GitHubCredentials,
    delete_connection,
    save_connection,
)
from ruleset.monitoring.evidence import EvidenceRecord, list_evidence
from ruleset.monitoring.runner import EvidenceRun, run_aws_checks, run_github_checks
from ruleset.osint.snapshot import SecurityPostureSnapshot
from ruleset.posture_service import collect_posture
from ruleset.questionnaires import AnswerRecord, AnswerReview, list_answers, review_answer
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
app = FastAPI(title="GRC Sentinel API")
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


@app.post(
    "/api/engagements/{engagement_id}/audit-shares",
    response_model=AuditShareCreated,
    status_code=status.HTTP_201_CREATED,
)
def post_audit_share(
    engagement_id: UUID, payload: AuditShareCreate, identity: CurrentTenant
) -> AuditShareCreated:
    expires_at = datetime.now(UTC) + timedelta(hours=payload.expires_in_hours)
    try:
        token = create_share_link(engine, identity.org_id, engagement_id, expires_at)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return AuditShareCreated(token=token, expires_at=expires_at)


@app.delete("/api/audit-shares/{token}", status_code=status.HTTP_204_NO_CONTENT)
def remove_audit_share(token: str, identity: CurrentTenant) -> Response:
    if not revoke_share(engine, identity.org_id, token):
        raise HTTPException(status_code=404, detail="share not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/tenant", response_model=TenantIdentity)
def current_tenant(identity: CurrentTenant) -> TenantIdentity:
    """Prove the verified Clerk organization-to-RLS tenant mapping."""
    return identity


@app.get("/api/frameworks", response_model=list[FrameworkOption])
def get_frameworks(identity: CurrentTenant) -> list[FrameworkOption]:
    return list_frameworks(engine)


@app.get("/api/framework-drift", response_model=FrameworkImpact)
def get_framework_drift(old: UUID, new: UUID, identity: CurrentTenant) -> FrameworkImpact:
    try:
        return framework_impact(engine, identity.org_id, old, new)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


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
def remove_connection(provider: Literal["github", "aws"], identity: CurrentTenant) -> Response:
    if not delete_connection(engine, identity.org_id, provider):
        raise HTTPException(status_code=404, detail="connection not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/evidence", response_model=list[EvidenceRecord])
def get_evidence(identity: CurrentTenant) -> list[EvidenceRecord]:
    return list_evidence(engine, identity.org_id)


@app.get("/api/questionnaire-answers", response_model=list[AnswerRecord])
def get_questionnaire_answers(identity: CurrentTenant) -> list[AnswerRecord]:
    return list_answers(engine, identity.org_id)


@app.get("/api/policies", response_model=list[PolicySummary])
def get_policies(identity: CurrentTenant) -> list[PolicySummary]:
    return list_policies(engine, identity.org_id)


@app.get("/api/model-usage", response_model=UsageSummary)
def get_model_usage(identity: CurrentTenant) -> UsageSummary:
    return summarize_usage(engine, identity.org_id)


@app.get("/api/policies/{policy_id}/docx")
def get_policy_docx(policy_id: UUID, identity: CurrentTenant) -> Response:
    try:
        filename, content = export_stored_policy(engine, identity.org_id, policy_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.patch("/api/questionnaire-answers/{answer_id}", status_code=status.HTTP_204_NO_CONTENT)
def patch_questionnaire_answer(
    answer_id: UUID, payload: AnswerReview, identity: CurrentTenant
) -> Response:
    if not review_answer(
        engine,
        identity.org_id,
        answer_id,
        payload.status,
        edited_answer=payload.edited_answer,
    ):
        raise HTTPException(status_code=404, detail="pending answer not found")
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
    return create_engagement(engine, identity.org_id, identity.user_id, payload)


@app.get("/api/engagements", response_model=list[EngagementSummary])
def get_engagements(identity: CurrentTenant) -> list[EngagementSummary]:
    return list_engagements(engine, identity.org_id)


@app.get(
    "/api/engagements/{engagement_id}/assurance-readiness",
    response_model=list[AssuranceReadiness],
)
def get_engagement_assurance_readiness(
    engagement_id: UUID, identity: CurrentTenant
) -> list[AssuranceReadiness]:
    return get_assurance_readiness(engine, identity.org_id, engagement_id)


@app.get("/api/engagements/{engagement_id}/coverage", response_model=list[CoverageRow])
def get_coverage(engagement_id: UUID, identity: CurrentTenant) -> list[CoverageRow]:
    return list_coverage_results(engine, identity.org_id, engagement_id)


@app.post("/api/engagements/{engagement_id}/uploads/{upload_id}/analyze")
async def post_coverage_analysis(
    engagement_id: UUID, upload_id: UUID, identity: CurrentTenant
) -> dict[str, int]:
    async def call(prompt: str, schema: dict[str, object]):
        return await call_model_json(
            prompt,
            schema,
            base_url=settings.llm_base_url,
            model=settings.llm_verifier_model,
            max_tokens=500,
            api_key=settings.llm_api_key.get_secret_value() if settings.llm_api_key else None,
        )

    try:
        analyzed = await analyze_upload_coverage(
            engine, identity.org_id, engagement_id, upload_id, call
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"analyzed_controls": analyzed}


@app.delete("/api/engagements/{engagement_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_engagement(engagement_id: UUID, identity: CurrentTenant) -> Response:
    if not delete_engagement(engine, identity.org_id, engagement_id):
        raise HTTPException(status_code=404, detail="engagement not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get(
    "/api/engagements/{engagement_id}/posture",
    response_model=SecurityPostureSnapshot,
)
async def get_posture(engagement_id: UUID, identity: CurrentTenant) -> SecurityPostureSnapshot:
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
            partial(
                ollama_embed,
                base_url=settings.ollama_base_url,
                model=settings.ollama_embedding_model,
            ),
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
