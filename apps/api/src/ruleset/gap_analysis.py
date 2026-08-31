from typing import Literal
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Engine, bindparam, text


class CoverageMatch(BaseModel):
    """The best uploaded section for one required control."""

    control_id: UUID
    control_code: str
    control_text: str
    chunk_id: UUID | None
    document_text: str | None
    similarity: float | None
    status: Literal["candidate", "missing"]


class RequiredControl(BaseModel):
    id: UUID
    code: str
    title: str
    description: str


def list_required_controls(
    engine: Engine, org_id: UUID, engagement_id: UUID
) -> list[RequiredControl]:
    """Return controls required by applicable regulations or selected assurance frameworks."""
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        rows = connection.execute(
            text(
                "SELECT DISTINCT c.id, c.control_code AS code, c.title, c.description "
                "FROM controls c WHERE c.id IN ("
                " SELECT rc.control_id FROM determinations d JOIN regulation_controls rc "
                " ON rc.regulation_id = d.regulation_id WHERE d.engagement_id = :engagement_id"
                ") OR c.framework_id IN ("
                " SELECT framework_id FROM assurance_objectives WHERE engagement_id = :engagement_id"
                ") ORDER BY c.control_code"
            ),
            {"engagement_id": engagement_id},
        ).mappings()
    return [RequiredControl.model_validate(row) for row in rows]


def find_coverage_candidates(
    engine: Engine,
    org_id: UUID,
    upload_id: UUID,
    control_ids: list[UUID],
    *,
    threshold: float = 0.75,
) -> list[CoverageMatch]:
    """Find each control's closest tenant-visible upload section using cosine similarity."""
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    if not control_ids:
        return []
    statement = text(
        "SELECT c.id AS control_id, c.control_code, "
        "concat_ws(': ', c.title, c.description) AS control_text, "
        "match.chunk_id, match.document_text, match.similarity "
        "FROM controls c JOIN control_embeddings ce ON ce.control_id = c.id "
        "LEFT JOIN LATERAL ("
        " SELECT uc.id AS chunk_id, uc.text AS document_text, "
        "1 - (uc.embedding <=> ce.embedding) AS similarity"
        " FROM upload_chunks uc WHERE uc.upload_id = :upload_id AND uc.embedding IS NOT NULL"
        " ORDER BY uc.embedding <=> ce.embedding LIMIT 1"
        ") match ON TRUE WHERE c.id IN :control_ids ORDER BY c.control_code"
    ).bindparams(bindparam("control_ids", expanding=True))
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        rows = connection.execute(
            statement, {"upload_id": upload_id, "control_ids": control_ids}
        ).mappings()
        return [
            CoverageMatch(
                **row,
                status="candidate"
                if row["similarity"] is not None and row["similarity"] >= threshold
                else "missing",
            )
            for row in rows
        ]
