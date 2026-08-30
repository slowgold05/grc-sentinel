from collections.abc import Callable
import json
from uuid import UUID

import httpx
from pydantic import BaseModel
from sqlalchemy import Engine, bindparam, text


class VoyageEmbedding(BaseModel):
    """One indexed vector returned by Voyage."""

    index: int
    embedding: list[float]


class VoyageResponse(BaseModel):
    """Validated subset of a Voyage embeddings response."""

    data: list[VoyageEmbedding]


def voyage_embed(texts: list[str], *, api_key: str, model: str) -> list[list[float]]:
    """Create 1,024-dimensional document embeddings through Voyage."""
    payload = json.dumps(
        {
            "input": texts,
            "model": model,
            "input_type": "document",
            "output_dimension": 1024,
        }
    ).encode()
    response = httpx.post(
        "https://api.voyageai.com/v1/embeddings",
        content=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        timeout=60,
    )
    response.raise_for_status()
    result = VoyageResponse.model_validate_json(response.content)
    return [item.embedding for item in sorted(result.data, key=lambda item: item.index)]


def embed_controls(
    engine: Engine,
    embed: Callable[[list[str]], list[list[float]]],
    *,
    control_ids: list[UUID] | None = None,
    batch_size: int = 128,
) -> int:
    """Embed controls missing vectors and idempotently store each chunk."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    query = (
        "SELECT c.id, c.control_code, c.title, c.description FROM controls c "
        "LEFT JOIN control_embeddings e ON e.control_id = c.id "
        "WHERE e.control_id IS NULL"
    )
    parameters: dict[str, object] = {}
    if control_ids is not None:
        if not control_ids:
            return 0
        query += " AND c.id IN :control_ids"
        parameters["control_ids"] = control_ids
    statement = text(query)
    if control_ids is not None:
        statement = statement.bindparams(bindparam("control_ids", expanding=True))

    with engine.begin() as connection:
        rows = connection.execute(statement, parameters).mappings().all()
        for start in range(0, len(rows), batch_size):
            batch = rows[start : start + batch_size]
            chunks = [f"{row['control_code']}: {row['title']}\n{row['description']}" for row in batch]
            vectors = embed(chunks)
            if len(vectors) != len(batch) or any(len(vector) != 1024 for vector in vectors):
                raise ValueError("embedding response must contain one 1024-dimension vector per control")
            connection.execute(
                text(
                    "INSERT INTO control_embeddings (control_id, embedding, chunk_text) "
                    "VALUES (:control_id, CAST(:embedding AS vector), :chunk_text) "
                    "ON CONFLICT (control_id) DO UPDATE SET embedding = EXCLUDED.embedding, "
                    "chunk_text = EXCLUDED.chunk_text"
                ),
                [
                    {
                        "control_id": row["id"],
                        "embedding": json.dumps(vector),
                        "chunk_text": chunk,
                    }
                    for row, chunk, vector in zip(batch, chunks, vectors, strict=True)
                ],
            )
    return len(rows)
