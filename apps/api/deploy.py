"""Prepare the production database, then start the API."""

import os
import subprocess

import psycopg
from psycopg import sql


owner_url = os.environ["MIGRATION_DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")
app_password = os.environ["APP_DATABASE_PASSWORD"]

with psycopg.connect(owner_url, autocommit=True) as connection:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = 'ruleset_app'")
        if cursor.fetchone() is None:
            cursor.execute(
                sql.SQL(
                    "CREATE ROLE ruleset_app LOGIN PASSWORD {} "
                    "NOSUPERUSER NOCREATEDB NOCREATEROLE"
                ).format(sql.Literal(app_password))
            )
        cursor.execute("SELECT current_database()")
        database_name = cursor.fetchone()[0]
        cursor.execute(
            sql.SQL("GRANT CONNECT ON DATABASE {} TO ruleset_app").format(
                sql.Identifier(database_name)
            )
        )
        cursor.execute("GRANT USAGE ON SCHEMA public TO ruleset_app")
        cursor.execute(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
            "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ruleset_app"
        )
        cursor.execute(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
            "GRANT USAGE, SELECT ON SEQUENCES TO ruleset_app"
        )

subprocess.run(["alembic", "upgrade", "head"], check=True)

with psycopg.connect(owner_url, autocommit=True) as connection:
    with connection.cursor() as cursor:
        cursor.execute(
            "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES "
            "IN SCHEMA public TO ruleset_app"
        )
        cursor.execute(
            "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ruleset_app"
        )

os.execvp(
    "uvicorn",
    [
        "uvicorn",
        "ruleset.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        os.getenv("PORT", "8000"),
    ],
)
