from collections.abc import Callable
from functools import partial
import json
from uuid import UUID

import httpx
from pydantic import BaseModel
from sqlalchemy import Engine, bindparam, text

from ruleset.config import settings
from ruleset.database import engine


class OllamaEmbedding(BaseModel):
    """One indexed vector returned by Ollama."""

    index: int
    embedding: list[float]


class OllamaEmbeddingResponse(BaseModel):
    """Validated subset of an OpenAI-compatible embeddings response."""

    data: list[OllamaEmbedding]


def ollama_embed(
    texts: list[str],
    *,
    base_url: str,
    model: str,
    transport: httpx.BaseTransport | None = None,
) -> list[list[float]]:
    """Create 1,024-dimensional embeddings through local Ollama."""
    payload = json.dumps(
        {
            "input": texts,
            "model": model,
            "dimensions": 1024,
        }
    ).encode()
    with httpx.Client(base_url=base_url, transport=transport, timeout=120) as client:
        response = client.post(
            "/embeddings",
            content=payload,
            headers={"Content-Type": "application/json"},
        )
    response.raise_for_status()
    result = OllamaEmbeddingResponse.model_validate_json(response.content)
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


def main() -> None:
    """Embed every control that is not already indexed by local Ollama."""
    embed_controls(
        engine,
        partial(
            ollama_embed,
            base_url=settings.ollama_base_url,
            model=settings.ollama_embedding_model,
        ),
    )


if __name__ == "__main__":
    main()
