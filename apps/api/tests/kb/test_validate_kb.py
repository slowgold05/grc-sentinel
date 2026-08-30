from uuid import uuid4

from sqlalchemy import create_engine, text

from ruleset.config import settings
from ruleset.kb.validate_kb import validate_kb


def test_detects_unreachable_soc2_control() -> None:
    engine = create_engine(str(settings.database_url))
    control_id = uuid4()
    with engine.begin() as connection:
        framework_id = connection.execute(
            text("SELECT id FROM frameworks WHERE name = 'SOC 2 TSC' LIMIT 1")
        ).scalar_one_or_none()
        if framework_id is None:
            framework_id = connection.execute(
                text(
                    "INSERT INTO frameworks "
                    "(name, version, publisher, machine_readable_source) "
                    "VALUES ('SOC 2 TSC', 'test', 'test', 'test') RETURNING id"
                )
            ).scalar_one()
        connection.execute(
            text(
                "INSERT INTO controls "
                "(id, framework_id, control_code, title, description) "
                "VALUES (:id, :framework_id, 'TEST-UNREACHABLE', 'Test', '')"
            ),
            {"id": control_id, "framework_id": framework_id},
        )

    try:
        result = validate_kb(engine)
        assert result.orphan_crosswalks == 0
        assert "TEST-UNREACHABLE" in result.unreachable_soc2_controls
        assert not result.valid
    finally:
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM controls WHERE id = :id"), {"id": control_id})
