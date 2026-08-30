from uuid import uuid4

from sqlalchemy import create_engine, text

from ruleset.config import settings
from ruleset.kb.embed_controls import embed_controls


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
