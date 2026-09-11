from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import text

from ruleset.auth import TenantIdentity, require_tenant
from ruleset.database import engine
from ruleset.main import app


def _identity(org_id: UUID, user: str) -> TenantIdentity:
    return TenantIdentity(org_id=org_id, user_id=user, provider_org_id=f"org_{org_id}")


def test_ai_system_api_enforces_tenant_and_approval_boundaries() -> None:
    """Create, read, transition, audit, isolate, and cascade-delete an AI system."""
    org_a, org_b, engagement_id = uuid4(), uuid4(), uuid4()
    with engine.begin() as connection:
        for org_id in (org_a, org_b):
            connection.execute(
                text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)}
            )
            connection.execute(
                text("INSERT INTO orgs (id, name) VALUES (:id, :name)"),
                {"id": org_id, "name": f"AI inventory {org_id}"},
            )
        connection.execute(
            text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_a)}
        )
        connection.execute(
            text("INSERT INTO engagements (id, org_id, company, expires_at) VALUES "
                 "(:id, :org_id, '{}', now() + interval '1 day')"),
            {"id": engagement_id, "org_id": org_a},
        )

    client = TestClient(app)
    payload = {
        "engagement_id": str(engagement_id),
        "name": "LedgerPeak Support Assistant",
        "description": "Drafts support replies for human review.",
        "owner": "Customer Operations",
        "business_purpose": "Reduce response drafting time.",
        "profile": {
            "operator_roles": ["deployer"],
            "model_name": "qwen3:14b",
            "vendor": "Ollama local",
            "intended_users": ["support agents"],
            "affected_persons": ["customers"],
            "decision_impact": "Draft only; a person decides whether to send.",
            "data_categories": ["support tickets"],
            "geographies": ["Singapore", "United States"],
            "external_access": False,
            "autonomy": "drafting only",
            "tool_access": False,
            "human_oversight": "A support agent reviews every draft.",
        },
    }
    try:
        app.dependency_overrides[require_tenant] = lambda: _identity(org_a, "owner_a")
        created = client.post("/api/ai-systems", json=payload)
        assert created.status_code == 201
        system_id = created.json()["id"]
        assert created.json()["status"] == "draft"
        assert client.get("/api/ai-systems").json()[0]["id"] == system_id
        assert client.get(f"/api/ai-systems/{system_id}").status_code == 200
        triage = client.get(f"/api/ai-systems/{system_id}/internal-risk")
        assert triage.status_code == 200
        assert triage.json()["rating"] == "needs_review"
        assert "decision_consequence" in triage.json()["missing_facts"]
        objective = client.post(
            f"/api/ai-systems/{system_id}/objectives",
            json={
                "framework": "iso_42001",
                "basis": "customer_contract",
                "scope": "Support assistant lifecycle",
                "target_date": "2027-01-31",
            },
        )
        assert objective.status_code == 201
        assert objective.json()["objective_type"] == "certifiable"
        assert objective.json()["source_version"] == "2023"
        assert objective.json()["selected_by"] == "owner_a"
        assert len(client.get(f"/api/ai-systems/{system_id}/objectives").json()) == 1
        assert client.post(
            f"/api/ai-systems/{system_id}/objectives",
            json={"framework": "iso_42001", "basis": "company_strategy", "scope": "AI"},
        ).status_code == 409
        empty_assessment = {name: "" for name in (
            "purpose_limitations", "stakeholders", "benefits_harms", "data_provenance",
            "privacy", "contextual_fairness", "explainability", "security", "robustness",
            "human_oversight", "vendor_reliance", "misuse", "incident_response", "monitoring",
            "decommissioning",
        )}
        assert client.patch(
            f"/api/ai-systems/{system_id}/impact-assessment", json=empty_assessment
        ).status_code == 200
        first_version = client.post(
            f"/api/ai-systems/{system_id}/impact-assessment/submit"
        ).json()
        assert first_version["version"] == 1
        assert first_version["status"] == "needs_review"
        assert len(first_version["missing_facts"]) == 15
        complete_assessment = {name: f"Reviewed {name}" for name in empty_assessment}
        client.patch(
            f"/api/ai-systems/{system_id}/impact-assessment", json=complete_assessment
        )
        second_version = client.post(
            f"/api/ai-systems/{system_id}/impact-assessment/submit"
        ).json()
        assert second_version["version"] == 2
        assert second_version["status"] == "complete"
        assert second_version["reviewer"] is None
        assert second_version["source_versions"]["nist_ai_rmf"] == "1.0"
        assert len(client.get(f"/api/ai-systems/{system_id}/impact-assessments").json()) == 2
        first_decision = client.post(
            f"/api/ai-systems/{system_id}/decisions",
            json={
                "decision_type": "assessment",
                "outcome": "conditional",
                "rationale": "Address monitoring actions before deployment.",
                "assessment_version_id": second_version["id"],
            },
        )
        assert first_decision.status_code == 201
        assert first_decision.json()["decided_by"] == "owner_a"
        assert first_decision.json()["supersedes_id"] is None
        replacement = client.post(
            f"/api/ai-systems/{system_id}/decisions",
            json={
                "decision_type": "assessment",
                "outcome": "approved",
                "rationale": "Monitoring actions were verified.",
                "assessment_version_id": second_version["id"],
                "expected_latest_decision_id": first_decision.json()["id"],
            },
        )
        assert replacement.status_code == 201
        assert replacement.json()["supersedes_id"] == first_decision.json()["id"]
        assert client.post(
            f"/api/ai-systems/{system_id}/decisions",
            json={
                "decision_type": "assessment",
                "outcome": "rejected",
                "rationale": "Stale review attempt.",
                "assessment_version_id": second_version["id"],
                "expected_latest_decision_id": first_decision.json()["id"],
            },
        ).status_code == 409
        history = client.get(f"/api/ai-systems/{system_id}/decisions").json()
        assert len(history) == 2
        for decision_type in ("deployment", "material_change", "exception", "retirement"):
            response = client.post(
                f"/api/ai-systems/{system_id}/decisions",
                json={
                    "decision_type": decision_type,
                    "outcome": "conditional" if decision_type == "exception" else "approved",
                    "rationale": f"Reviewed {decision_type} decision.",
                },
            )
            assert response.status_code == 201
        assert {
            item["decision_type"]
            for item in client.get(f"/api/ai-systems/{system_id}/decisions").json()
        } == {"assessment", "deployment", "material_change", "exception", "retirement"}
        assert client.post(
            f"/api/ai-systems/{system_id}/decisions",
            json={
                "decision_type": "assessment",
                "outcome": "approved",
                "rationale": "Missing version.",
            },
        ).status_code == 422
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_a)}
            )
            assert connection.execute(
                text("UPDATE ai_governance_decisions SET rationale = 'changed' WHERE id = :id"),
                {"id": first_decision.json()["id"]},
            ).rowcount == 0
            assert connection.execute(
                text("DELETE FROM ai_governance_decisions WHERE id = :id"),
                {"id": first_decision.json()["id"]},
            ).rowcount == 0
        transitioned = client.patch(
            f"/api/ai-systems/{system_id}/status", json={"status": "in_review"}
        )
        assert transitioned.status_code == 200
        assert transitioned.json()["status"] == "in_review"
        assert client.patch(
            f"/api/ai-systems/{system_id}/status", json={"status": "deployed"}
        ).status_code == 409

        app.dependency_overrides[require_tenant] = lambda: _identity(org_b, "owner_b")
        assert client.get("/api/ai-systems").json() == []
        assert client.get(f"/api/ai-systems/{system_id}").status_code == 404
        assert client.get(f"/api/ai-systems/{system_id}/internal-risk").status_code == 404
        assert client.get(f"/api/ai-systems/{system_id}/objectives").json() == []
        assert client.post(
            f"/api/ai-systems/{system_id}/objectives",
            json={"framework": "nist_ai_rmf", "basis": "company_strategy", "scope": "AI"},
        ).status_code == 404
        assert client.get(f"/api/ai-systems/{system_id}/impact-assessments").json() == []
        assert client.get(f"/api/ai-systems/{system_id}/decisions").json() == []
        assert client.post(
            f"/api/ai-systems/{system_id}/decisions",
            json={
                "decision_type": "deployment",
                "outcome": "approved",
                "rationale": "Cross-tenant attempt.",
            },
        ).status_code == 404
        assert client.patch(
            f"/api/ai-systems/{system_id}/status", json={"status": "retired"}
        ).status_code == 404

        app.dependency_overrides[require_tenant] = lambda: _identity(org_a, "owner_a")
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_a)}
            )
            assert connection.execute(
                text("SELECT count(*) FROM audit_events WHERE engagement_id = :id "
                     "AND event_type LIKE 'ai_system_%'"),
                {"id": engagement_id},
            ).scalar_one() == 2
        assert client.delete(f"/api/engagements/{engagement_id}").status_code == 204
        assert client.get("/api/ai-systems").json() == []
    finally:
        app.dependency_overrides.clear()
        for org_id in (org_a, org_b):
            with engine.begin() as connection:
                connection.execute(
                    text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)}
                )
                connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
