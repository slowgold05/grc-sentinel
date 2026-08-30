from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from ruleset.config import settings

config = context.config
config.set_main_option("sqlalchemy.url", str(settings.migration_database_url))
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = None


def run_migrations_offline() -> None:
    """Run migrations without creating a database connection."""
    context.configure(url=str(settings.migration_database_url), literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against the configured database."""
    with engine_from_config(config.get_section(config.config_ini_section), poolclass=pool.NullPool).connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_offline() if context.is_offline_mode() else run_migrations_online()
