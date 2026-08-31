from collections.abc import Callable
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Engine, text

from ruleset.uploads.chunks import store_sections
from ruleset.uploads.embed_chunks import embed_sections
from ruleset.uploads.parse_worker import parse_document
from ruleset.uploads.store import store_upload
from ruleset.uploads.validation import validate_upload


class IngestedDocument(BaseModel):
    id: UUID
    sections: int
    embedded_sections: int
    sha256: str


def ingest_document(
    engine: Engine,
    org_id: UUID,
    engagement_id: UUID,
    filename: str,
    content: bytes,
    master_key: bytes,
    embed: Callable[[list[str]], list[list[float]]],
) -> IngestedDocument:
    """Validate, parse, encrypt, and store one tenant document."""
    metadata = validate_upload(filename, content)
    document = parse_document(content, metadata.media_type)
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        if connection.execute(
            text("SELECT 1 FROM engagements WHERE id = :id"), {"id": engagement_id}
        ).scalar_one_or_none() is None:
            raise LookupError("engagement not found")
    upload_id = store_upload(engine, org_id, engagement_id, metadata, content, master_key)
    sections = store_sections(engine, org_id, upload_id, document)
    embedded_sections = embed_sections(engine, org_id, upload_id, embed)
    return IngestedDocument(
        id=upload_id,
        sections=sections,
        embedded_sections=embedded_sections,
        sha256=metadata.sha256,
    )
