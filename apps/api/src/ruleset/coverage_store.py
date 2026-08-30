from uuid import UUID

from sqlalchemy import Engine, text

from ruleset.coverage_verifier import CoverageVerification


def store_coverage_results(
    engine: Engine,
    org_id: UUID,
    engagement_id: UUID,
    upload_id: UUID,
    results: list[CoverageVerification],
) -> int:
    """Append deterministically accepted coverage results for one tenant."""
    if any(not result.accepted for result in results):
        raise ValueError("unverified coverage result cannot be stored")
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        for result in results:
            claim = result.claim
            connection.execute(
                text(
                    "INSERT INTO coverage_results "
                    "(org_id, engagement_id, upload_id, control_id, chunk_id, status, evidence_quote, gap) "
                    "VALUES (:org_id, :engagement_id, :upload_id, :control_id, :chunk_id, :status, "
                    ":evidence_quote, :gap)"
                ),
                {
                    "org_id": org_id,
                    "engagement_id": engagement_id,
                    "upload_id": upload_id,
                    "control_id": claim.control_id,
                    "chunk_id": claim.chunk_id,
                    "status": claim.status,
                    "evidence_quote": claim.evidence_quote,
                    "gap": claim.gap,
                },
            )
    return len(results)
