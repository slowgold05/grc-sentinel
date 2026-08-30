from os import urandom
from uuid import uuid4

import httpx
from sqlalchemy import create_engine, text

from ruleset.config import settings
from ruleset.monitoring.aws import AwsConnection
from ruleset.monitoring.connections import AwsCredentials, GitHubCredentials, save_connection
from ruleset.monitoring.runner import run_aws_checks, run_github_checks


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


def test_runner_assumes_role_and_appends_all_aws_evidence(monkeypatch: object) -> None:
    engine, org_id, master_key = create_engine(str(settings.database_url)), uuid4(), urandom(32)
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        connection.execute(text("INSERT INTO orgs (id, name) VALUES (:id, 'aws runner')"), {"id": org_id})
    save_connection(
        engine,
        org_id,
        AwsCredentials(
            provider="aws",
            role_arn="arn:aws:iam::123456789012:role/RulesetReadOnly",
            external_id="tenant-secret",
            region="us-east-1",
        ),
        master_key,
    )

    class S3:
        def list_buckets(self) -> dict[str, list[object]]:
            return {"Buckets": []}

    class CloudTrail:
        def describe_trails(self, **_: object) -> dict[str, list[dict[str, str]]]:
            return {"trailList": [{"Name": "main", "TrailARN": "arn:trail"}]}

        def get_trail_status(self, **_: object) -> dict[str, bool]:
            return {"IsLogging": True}

    class Iam:
        def get_paginator(self, _: str) -> object:
            return type("Paginator", (), {"paginate": lambda self: [{"Users": []}]})()

    monkeypatch.setattr(
        AwsConnection,
        "from_assumed_role",
        lambda *_: AwsConnection(S3(), CloudTrail(), Iam()),
    )
    try:
        runs = run_aws_checks(engine, org_id, master_key)
        assert [run.result.status for run in runs] == ["pass", "pass", "pass"]
    finally:
        with engine.begin() as connection:
            connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
