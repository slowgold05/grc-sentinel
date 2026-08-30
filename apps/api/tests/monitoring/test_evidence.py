from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import create_engine, text

from ruleset.config import settings
from ruleset.monitoring.evidence import append_evidence, is_control_drift, list_evidence
from ruleset.monitoring.github import GitHubOrgMfaTest
from ruleset.monitoring.models import TestResult as ControlTestResult


def test_evidence_is_tenant_scoped_and_immutable() -> None:
    engine = create_engine(str(settings.database_url))
    org_id = uuid4()
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        connection.execute(
            text("INSERT INTO orgs (id, name) VALUES (:id, 'evidence test')"), {"id": org_id}
        )
    try:
        tested_at = datetime.now(UTC)
        write = append_evidence(
            engine,
            org_id,
            GitHubOrgMfaTest(),
            ControlTestResult(
                status="pass", observed={"enabled": True}, tested_at=tested_at
            ),
            {"two_factor_requirement_enabled": True},
        )
        records = list_evidence(engine, org_id)
        assert records[0].id == write.id
        assert not write.drift
        assert records[0].control_ids == ["IA-2", "CC6.1"]
        drift = append_evidence(
            engine,
            org_id,
            GitHubOrgMfaTest(),
            ControlTestResult(
                status="fail", observed={"enabled": False}, tested_at=tested_at + timedelta(seconds=1)
            ),
            {"two_factor_requirement_enabled": False},
        )
        assert drift.drift
        assert list_evidence(engine, org_id)[0].drift
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)}
            )
            assert connection.execute(
                text("SELECT status FROM control_evidence WHERE id = :id"), {"id": write.id}
            ).scalar_one() == "pass"
            assert connection.execute(
                text("UPDATE control_evidence SET status = 'fail' WHERE id = :id"),
                {"id": write.id},
            ).rowcount == 0
    finally:
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)}
            )
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})


def test_only_pass_to_fail_is_control_drift() -> None:
    assert is_control_drift("pass", "fail") is True
    assert is_control_drift("fail", "fail") is False
    assert is_control_drift(None, "fail") is False
