import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import text

from ruleset.ai_governance import policy_suite
from ruleset.ai_governance.policy_suite import (
    AIPolicyDraftRequest,
    AIPolicyType,
    generate_ai_policy,
    prepare_ai_policy_context,
)
from ruleset.database import engine
from ruleset.generation.openai_compatible_client import ModelResult


def test_exposes_all_ten_separate_policy_types() -> None:
    assert len(AIPolicyType) == 10


def test_retrieves_only_controls_from_selected_objective(monkeypatch) -> None:
    org_id, engagement_id, system_id, framework_id = uuid4(), uuid4(), uuid4(), uuid4()
    monkeypatch.setitem(
        policy_suite._OBJECTIVE_CORPORA,
        "nist_ai_rmf",
        ("NIST AI RMF test", "test-only", "voluntary framework"),
    )
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        connection.execute(text("INSERT INTO orgs (id, name) VALUES (:id, 'policy suite')"), {"id": org_id})
        connection.execute(
            text("INSERT INTO engagements (id, org_id, company, expires_at) VALUES (:id, :org, '{}', :expires)"),
            {"id": engagement_id, "org": org_id, "expires": datetime.now(UTC) + timedelta(days=1)},
        )
        connection.execute(
            text("INSERT INTO ai_systems (id, org_id, engagement_id, name, description, owner_name, business_purpose, profile) VALUES (:id, :org, :engagement, 'Assistant', 'Test', 'Owner', 'Test', '{}')"),
            {"id": system_id, "org": org_id, "engagement": engagement_id},
        )
        connection.execute(
            text("INSERT INTO ai_assurance_objectives (org_id, engagement_id, ai_system_id, framework, source_version, objective_type, basis, scope, selected_by) VALUES (:org, :engagement, :system, 'nist_ai_rmf', '1.0', 'voluntary', 'company_strategy', 'test', 'reviewer')"),
            {"org": org_id, "engagement": engagement_id, "system": system_id},
        )
        connection.execute(
            text("INSERT INTO frameworks (id, name, version, publisher, machine_readable_source) VALUES (:id, 'NIST AI RMF test', 'test-only', 'NIST', 'https://example.test')"),
            {"id": framework_id},
        )
        connection.execute(
            text("INSERT INTO controls (framework_id, control_code, title, description) VALUES (:id, 'GOVERN 1.1', 'Outcome', 'Outcome text')"),
            {"id": framework_id},
        )
    try:
        context = prepare_ai_policy_context(
            engine, org_id, system_id, AIPolicyType.GOVERNANCE, ["GOVERN 1.1"]
        )
        assert [item.control_id for item in context.controls] == ["GOVERN 1.1"]
        assert context.sources[0].classification == "voluntary framework"
        async def generate(_prompt, _schema):
            return ModelResult(
                text='{"statements":[{"text":"Maintain AI accountability.","control_ids":["GOVERN 1.1"]}]}',
                input_tokens=20,
                output_tokens=10,
            )

        async def verify(_prompt, _schema):
            return ModelResult(
                text='{"faithful":true,"issue":""}', input_tokens=10, output_tokens=3
            )

        draft = asyncio.run(
            generate_ai_policy(
                engine,
                org_id,
                system_id,
                AIPolicyType.GOVERNANCE,
                AIPolicyDraftRequest(control_ids=["GOVERN 1.1"]),
                generate,
                verify,
            )
        )
        assert draft.status == "draft"
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)}
            )
            stored = connection.execute(
                text("SELECT ai_system_id, source_versions FROM policies WHERE id = :id"),
                {"id": draft.id},
            ).mappings().one()
        assert stored["ai_system_id"] == system_id
        assert stored["source_versions"][0]["framework"] == "NIST AI RMF test"
        with pytest.raises(ValueError, match="not in a selected installed objective"):
            prepare_ai_policy_context(
                engine, org_id, system_id, AIPolicyType.GOVERNANCE, ["MADE-UP 1"]
            )
    finally:
        with engine.begin() as connection:
            connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
            connection.execute(text("DELETE FROM frameworks WHERE id = :id"), {"id": framework_id})
