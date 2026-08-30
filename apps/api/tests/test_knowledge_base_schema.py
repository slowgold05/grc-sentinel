from sqlalchemy import create_engine, text

from ruleset.config import settings


def test_knowledge_base_schema() -> None:
    """Verify every roadmap table and the 1024-dimensional vector column exist."""
    engine = create_engine(str(settings.database_url))
    with engine.connect() as connection:
        tables = set(connection.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")).scalars())
        vector_type = connection.execute(
            text(
                "SELECT format_type(a.atttypid, a.atttypmod) "
                "FROM pg_attribute a JOIN pg_class c ON c.oid = a.attrelid "
                "WHERE c.relname = 'control_embeddings' AND a.attname = 'embedding'"
            )
        ).scalar_one()
        control_columns = set(
            connection.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'controls'"
                )
            ).scalars()
        )

    assert {
        "frameworks",
        "controls",
        "crosswalks",
        "regulations",
        "regulation_controls",
        "control_embeddings",
        "policy_templates",
    } <= tables
    assert vector_type == "vector(1024)"
    assert {"valid_from", "valid_to"} <= control_columns
