from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from ruleset.ai_governance.evaluations import evaluation_result
from ruleset.ai_governance.models import EvaluationDefinitionCreate
from ruleset.ai_governance.models import AIChangeType
from ruleset.ai_governance.versions import approval_is_current
from ruleset.auth import TenantIdentity, require_tenant
from ruleset.database import engine
from ruleset.main import app


TYPES = (
    "task_performance", "robustness", "prompt_injection", "privacy_leakage",
    "groundedness", "harmful_output", "contextual_fairness", "oversight_effectiveness",
    "reliability",
)


@pytest.mark.parametrize("evaluation_type", TYPES)
def test_all_evaluation_dimensions_are_explicit(evaluation_type: str) -> None:
    """Accept every roadmap evaluation dimension without free-form categories."""
    model = EvaluationDefinitionCreate(
        evaluation_type=evaluation_type,
        name=f"{evaluation_type} check",
        dataset_name="Fictional fixed set",
        dataset_version="1",
        population_context="Synthetic portfolio fixtures only",
        metric_name="pass rate",
        metric_direction="higher_is_better",
        threshold=0.9,
        owner="AI assurance",
        cadence="before release",
        limitations="Does not establish broad model safety",
    )
    assert model.evaluation_type.value == evaluation_type


def test_metric_direction_determines_result() -> None:
    """Apply both threshold directions at their boundaries."""
    assert evaluation_result("higher_is_better", 0.9, 0.9) == "pass"
    assert evaluation_result("higher_is_better", 0.9, 0.89) == "fail"
    assert evaluation_result("lower_is_better", 0.1, 0.1) == "pass"
    assert evaluation_result("lower_is_better", 0.1, 0.11) == "fail"


def test_only_scoped_material_changes_invalidate_approval() -> None:
    """Keep unrelated approvals current while invalidating intersecting scopes."""
    assert approval_is_current([AIChangeType.MODEL], [AIChangeType.PROMPT])
    assert not approval_is_current(
        [AIChangeType.MODEL, AIChangeType.MEASURED_PERFORMANCE],
        [AIChangeType.MEASURED_PERFORMANCE],
    )


def test_evaluation_registry_is_tenant_safe_approved_and_append_only() -> None:
    """Version, approve, measure, isolate, preserve, and cascade evaluation evidence."""
    org_a, org_b, engagement_id, system_id = uuid4(), uuid4(), uuid4(), uuid4()
    with engine.begin() as connection:
        for org_id in (org_a, org_b):
            connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
            connection.execute(text("INSERT INTO orgs (id, name) VALUES (:id, :name)"), {"id": org_id, "name": f"eval {org_id}"})
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_a)})
        connection.execute(text("INSERT INTO engagements (id, org_id, company, expires_at) VALUES (:id, :org, '{}', now() + interval '1 day')"), {"id": engagement_id, "org": org_a})
        connection.execute(text("INSERT INTO ai_systems (id, org_id, engagement_id, name, description, owner_name, business_purpose, profile) VALUES (:id, :org, :engagement, 'Assistant', 'Test', 'Owner', 'Test', '{}')"), {"id": system_id, "org": org_a, "engagement": engagement_id})

    client = TestClient(app)
    definition_payload = {
        "evaluation_type": "groundedness",
        "name": "Citation groundedness",
        "dataset_name": "Fictional policy questions",
        "dataset_version": "fixture-v1",
        "population_context": "Portfolio demonstration prompts",
        "metric_name": "grounded answer rate",
        "metric_direction": "higher_is_better",
        "threshold": 0.95,
        "owner": "AI assurance",
        "cadence": "before release",
        "limitations": "Narrow fixed fixtures; not a broad safety claim",
    }
    run_payload = {
        "model_version": "qwen3:14b@sha256:fictional",
        "configuration_version": "grc-prompts-v1",
        "measured_value": 0.96,
        "summary": "Fixed fictional evaluation set",
    }
    try:
        app.dependency_overrides[require_tenant] = lambda: TenantIdentity(org_id=org_a, user_id="reviewer_a", provider_org_id="org_a")
        created = client.post(f"/api/ai-systems/{system_id}/evaluation-definitions", json=definition_payload)
        assert created.status_code == 201
        definition_id = created.json()["id"]
        assert created.json()["version"] == 1
        assert created.json()["latest_result"] is None
        assert created.json()["threshold_approved_by"] is None
        assert client.post(f"/api/ai-evaluation-definitions/{definition_id}/runs", json=run_payload).status_code == 409
        assert client.post(f"/api/ai-evaluation-definitions/{definition_id}/threshold-approval", json={"rationale": "Threshold reviewed against the fixed dataset."}).status_code == 204
        assert client.post(f"/api/ai-evaluation-definitions/{definition_id}/threshold-approval", json={"rationale": "Duplicate."}).status_code == 409
        passed = client.post(f"/api/ai-evaluation-definitions/{definition_id}/runs", json=run_payload)
        assert passed.status_code == 201
        assert passed.json()["result"] == "pass"
        assert passed.json()["drift"] is False
        assert passed.json()["definition_version"] == 1
        assert passed.json()["dataset_version"] == "fixture-v1"
        failed = client.post(f"/api/ai-evaluation-definitions/{definition_id}/runs", json=run_payload | {"measured_value": 0.8})
        assert failed.json()["result"] == "fail"
        assert failed.json()["drift"] is True
        assert client.get(f"/api/ai-evaluation-definitions/{definition_id}/runs").json()[1]["drift"] is False
        revised = client.post(
            f"/api/ai-systems/{system_id}/evaluation-definitions",
            json=definition_payload | {"dataset_version": "fixture-v2"},
        )
        assert revised.json()["version"] == 2
        definitions = client.get(f"/api/ai-systems/{system_id}/evaluation-definitions").json()
        assert definitions[0]["version"] == 2
        assert definitions[0]["latest_result"] is None
        assert definitions[1]["latest_result"] == "fail"
        assert definitions[1]["threshold_approved_by"] == "reviewer_a"
        assert len(client.get(f"/api/ai-evaluation-definitions/{definition_id}/runs").json()) == 2
        version_payload = {
            "model_version": "model-v1",
            "prompt_version": "prompt-v1",
            "corpus_version": "corpus-v1",
            "tool_permissions_version": "tools-v1",
            "purpose_version": "purpose-v1",
            "vendor_terms_version": "terms-v1",
            "material_changes": [],
        }
        baseline = client.post(f"/api/ai-systems/{system_id}/versions", json=version_payload)
        assert baseline.json()["version"] == 1
        assert baseline.json()["review_required"] is False
        changed = client.post(
            f"/api/ai-systems/{system_id}/versions",
            json=version_payload | {"model_version": "model-v2", "material_changes": ["model"]},
        )
        assert changed.json()["version"] == 2
        assert changed.json()["review_required"] is True
        assert client.get(f"/api/ai-systems/{system_id}/versions").json()[0]["material_changes"] == ["model"]
        with engine.begin() as connection:
            connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_a)})
            assert connection.execute(text("UPDATE ai_evaluation_runs SET result = 'pass' WHERE id = :id"), {"id": failed.json()["id"]}).rowcount == 0
            assert connection.execute(text("DELETE FROM ai_evaluation_definitions WHERE id = :id"), {"id": definition_id}).rowcount == 0

        app.dependency_overrides[require_tenant] = lambda: TenantIdentity(org_id=org_b, user_id="reviewer_b", provider_org_id="org_b")
        assert client.get(f"/api/ai-systems/{system_id}/evaluation-definitions").json() == []
        assert client.get(f"/api/ai-evaluation-definitions/{definition_id}/runs").json() == []
        assert client.get(f"/api/ai-systems/{system_id}/versions").json() == []
        assert client.post(f"/api/ai-evaluation-definitions/{definition_id}/runs", json=run_payload).status_code == 404

        app.dependency_overrides[require_tenant] = lambda: TenantIdentity(org_id=org_a, user_id="reviewer_a", provider_org_id="org_a")
        assert client.delete(f"/api/engagements/{engagement_id}").status_code == 204
        assert client.get(f"/api/ai-systems/{system_id}/evaluation-definitions").json() == []
    finally:
        app.dependency_overrides.clear()
        for org_id in (org_a, org_b):
            with engine.begin() as connection:
                connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
                connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
