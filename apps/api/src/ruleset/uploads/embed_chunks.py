from collections.abc import Callable
import json
from uuid import UUID

from sqlalchemy import Engine, text


def embed_sections(
    engine: Engine,
    org_id: UUID,
    upload_id: UUID,
    embed: Callable[[list[str]], list[list[float]]],
    *,
    batch_size: int = 128,
) -> int:
    """Embed unembedded sections for one tenant upload."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        rows = connection.execute(
            text(
                "SELECT id, text FROM upload_chunks "
                "WHERE upload_id = :upload_id AND embedding IS NULL ORDER BY seq"
            ),
            {"upload_id": upload_id},
        ).mappings().all()
        for start in range(0, len(rows), batch_size):
            batch = rows[start : start + batch_size]
            vectors = embed([row["text"] for row in batch])
            if len(vectors) != len(batch) or any(len(vector) != 1024 for vector in vectors):
                raise ValueError("embedding response must contain one 1024-dimension vector per section")
            connection.execute(
                text(
                    "UPDATE upload_chunks SET embedding = CAST(:embedding AS vector) "
                    "WHERE id = :id"
                ),
                [
                    {"id": row["id"], "embedding": json.dumps(vector)}
                    for row, vector in zip(batch, vectors, strict=True)
                ],
            )
    return len(rows)

