from uuid import UUID

from sqlalchemy import Engine, text

from ruleset.uploads.parse_worker import ParsedDocument


def store_sections(
    engine: Engine,
    org_id: UUID,
    upload_id: UUID,
    document: ParsedDocument,
) -> int:
    """Idempotently store non-empty parsed sections for one tenant upload."""
    sections = [section for section in document.sections if section.text.strip()]
    if not sections:
        return 0
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        connection.execute(
            text(
                "INSERT INTO upload_chunks (org_id, upload_id, seq, text) "
                "VALUES (:org_id, :upload_id, :seq, :text) "
                "ON CONFLICT (upload_id, seq) DO UPDATE SET text = EXCLUDED.text, embedding = NULL"
            ),
            [
                {
                    "org_id": org_id,
                    "upload_id": upload_id,
                    "seq": section.seq,
                    "text": section.text,
                }
                for section in sections
            ],
        )
    return len(sections)

