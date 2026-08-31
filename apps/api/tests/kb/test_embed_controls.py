from uuid import uuid4

import httpx
from sqlalchemy import create_engine, text

from ruleset.config import settings
from ruleset.kb.embed_controls import embed_controls, ollama_embed


def test_ollama_embed_uses_local_openai_endpoint() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "http://localhost:11434/v1/embeddings"
        assert request.headers.get("authorization") is None
        return httpx.Response(200, json={"data": [{"index": 0, "embedding": [0.0] * 1024}]})

    vectors = ollama_embed(
        ["control"],
        base_url="http://localhost:11434/v1",
        model="mxbai-embed-large",
        transport=httpx.MockTransport(handler),
    )
    assert len(vectors[0]) == 1024


def test_embeds_one_control_idempotently() -> None:
    engine = create_engine(str(settings.database_url))
    framework_id, control_id = uuid4(), uuid4()
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO frameworks "
                "(id, name, version, publisher, machine_readable_source) "
                "VALUES (:id, :name, '1', 'test', 'test')"
            ),
            {"id": framework_id, "name": f"test-{framework_id}"},
        )
        connection.execute(
            text(
                "INSERT INTO controls "
                "(id, framework_id, control_code, title, description) "
                "VALUES (:id, :framework_id, 'T-1', 'Test control', 'Test description')"
            ),
            {"id": control_id, "framework_id": framework_id},
        )

    try:
        def fake(chunks: list[str]) -> list[list[float]]:
            return [[0.0] * 1024 for _ in chunks]

        assert embed_controls(engine, fake, control_ids=[control_id]) == 1
        assert embed_controls(engine, fake, control_ids=[control_id]) == 0
    finally:
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM frameworks WHERE id = :id"), {"id": framework_id})
