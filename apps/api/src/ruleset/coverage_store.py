from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Engine, text

from ruleset.coverage_verifier import CoverageVerification


class CoverageRow(BaseModel):
    control: str
    title: str
    frameworks: list[str]
    status: str
    evidence: str
    gap: str


def list_coverage_results(
    engine: Engine, org_id: UUID, engagement_id: UUID
) -> list[CoverageRow]:
    """Return the newest stored result for each control in one engagement."""
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        rows = connection.execute(
            text(
                "SELECT DISTINCT ON (r.control_id) c.control_code AS control, c.title, "
                "ARRAY[f.name] AS frameworks, r.status, r.evidence_quote AS evidence, r.gap "
                "FROM coverage_results r JOIN controls c ON c.id = r.control_id "
                "JOIN frameworks f ON f.id = c.framework_id "
                "WHERE r.engagement_id = :engagement_id "
                "ORDER BY r.control_id, r.created_at DESC"
            ),
            {"engagement_id": engagement_id},
        ).mappings()
    return [CoverageRow.model_validate(row) for row in rows]


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
