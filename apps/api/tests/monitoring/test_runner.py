from os import urandom
from uuid import uuid4

import httpx
from sqlalchemy import create_engine, text

from ruleset.config import settings
from ruleset.monitoring.connections import GitHubCredentials, save_connection
from ruleset.monitoring.runner import run_github_checks


def test_runner_appends_all_github_evidence() -> None:
    engine, org_id, master_key = create_engine(str(settings.database_url)), uuid4(), urandom(32)
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        connection.execute(text("INSERT INTO orgs (id, name) VALUES (:id, 'runner test')"), {"id": org_id})
    save_connection(
        engine,
        org_id,
        GitHubCredentials(provider="github", organization="ruleset-demo", token="token"),
        master_key,
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/orgs/ruleset-demo":
            return httpx.Response(200, json={"two_factor_requirement_enabled": True})
        if request.url.path.endswith("/repos"):
            return httpx.Response(200, json=[])
        raise AssertionError(f"unexpected request: {request.url}")

    try:
        runs = run_github_checks(engine, org_id, master_key, httpx.MockTransport(handler))
        assert [run.result.status for run in runs] == ["pass", "pass", "pass"]
        with engine.begin() as connection:
            connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
            assert connection.execute(text("SELECT count(*) FROM control_evidence")).scalar_one() == 3
    finally:
        with engine.begin() as connection:
            connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
