from collections.abc import Awaitable, Callable
from uuid import UUID

from sqlalchemy import Engine, text

from ruleset.coverage_store import store_coverage_results
from ruleset.coverage_verifier import (
    CoverageClaim,
    CoverageResponse,
    CoverageVerification,
    build_verification_prompt,
    parse_coverage_claim,
    verify_evidence_quote,
)
from ruleset.gap_analysis import find_coverage_candidates, list_required_controls
from ruleset.generation.openai_compatible_client import ModelResult

ModelCall = Callable[[str, dict[str, object]], Awaitable[ModelResult]]


async def analyze_upload_coverage(
    engine: Engine,
    org_id: UUID,
    engagement_id: UUID,
    upload_id: UUID,
    call_model: ModelCall,
) -> int:
    """Retrieve, verify, and store coverage for every required control."""
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        exists = connection.execute(
            text("SELECT 1 FROM uploads WHERE id = :upload_id AND engagement_id = :engagement_id"),
            {"upload_id": upload_id, "engagement_id": engagement_id},
        ).scalar_one_or_none()
    if exists is None:
        raise LookupError("upload not found")
    controls = list_required_controls(engine, org_id, engagement_id)
    matches = find_coverage_candidates(engine, org_id, upload_id, [item.id for item in controls])
    results: list[CoverageVerification] = []
    for match in matches:
        if match.status == "missing" or match.chunk_id is None or match.document_text is None:
            results.append(
                verify_evidence_quote(
                    CoverageClaim(
                        control_id=match.control_id,
                        chunk_id=None,
                        status="missing",
                        evidence_quote="",
                        gap="No sufficiently similar policy evidence was found.",
                    ),
                    None,
                )
            )
            continue
        response = await call_model(
            build_verification_prompt(match.control_text, match.document_text),
            CoverageResponse.model_json_schema(),
        )
        claim = parse_coverage_claim(
            response.text, control_id=match.control_id, chunk_id=match.chunk_id
        )
        verification = verify_evidence_quote(claim, match.document_text)
        if not verification.accepted:
            raise ValueError(verification.reason)
        results.append(verification)
    return store_coverage_results(engine, org_id, engagement_id, upload_id, results)
