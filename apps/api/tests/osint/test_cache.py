from uuid import uuid4

from sqlalchemy import create_engine, text

from ruleset.config import settings
from ruleset.osint.cache import cache_result, load_cached_result


def test_cache_is_tenant_scoped_and_case_normalized() -> None:
    engine = create_engine(str(settings.database_url))
    org_a, org_b = uuid4(), uuid4()
    with engine.begin() as connection:
        for org_id in (org_a, org_b):
            connection.execute(
                text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)}
            )
            connection.execute(
                text("INSERT INTO orgs (id, name) VALUES (:id, 'cache test')"), {"id": org_id}
            )
    try:
        cache_result(engine, org_a, "Example.COM", "headers", {"grade": "A"})
        assert load_cached_result(engine, org_a, "example.com", "headers") == {"grade": "A"}
        assert load_cached_result(engine, org_b, "example.com", "headers") is None
    finally:
        with engine.begin() as connection:
            for org_id in (org_a, org_b):
                connection.execute(
                    text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)}
                )
                connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
