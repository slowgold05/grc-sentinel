import pytest
from sqlalchemy import text

from ruleset.database import engine


@pytest.fixture(scope="session", autouse=True)
def seed_minimal_control_catalog() -> None:
    """Keep database tests independent of locally imported OSCAL/SCF artifacts."""
    with engine.begin() as connection:
        for name, version in (
            ("ISO 27001", "2022"),
            ("SOC 2 TSC", "2017:2022"),
            ("PCI DSS", "4.0.1"),
        ):
            framework_id = connection.execute(
                text(
                    "INSERT INTO frameworks (name, version, publisher, machine_readable_source) "
                    "VALUES (:name, :version, 'test fixture', 'test fixture') "
                    "ON CONFLICT (name, version) DO UPDATE SET name = EXCLUDED.name RETURNING id"
                ),
                {"name": name, "version": version},
            ).scalar_one()
            connection.execute(
                text(
                    "INSERT INTO controls (framework_id, control_code, title, description) "
                    "VALUES (:framework_id, 'TEST-1', 'Test control', 'Test fixture only') "
                    "ON CONFLICT (framework_id, control_code) DO NOTHING"
                ),
                {"framework_id": framework_id},
            )
