from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import text

from ruleset.auth import TenantIdentity, require_tenant
from ruleset.database import engine
from ruleset.main import app


def test_risk_api_uses_authenticated_tenant() -> None:
    org_id = uuid4()
    engagement_id, ai_system_id = uuid4(), uuid4()
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        connection.execute(
            text("INSERT INTO orgs (id, name) VALUES (:id, 'risk api test')"), {"id": org_id}
        )
        connection.execute(
            text("INSERT INTO engagements (id, org_id, company, expires_at) VALUES (:id, :org, '{}', now() + interval '1 day')"),
            {"id": engagement_id, "org": org_id},
        )
        connection.execute(
            text("INSERT INTO ai_systems (id, org_id, engagement_id, name, description, owner_name, business_purpose, profile) VALUES (:id, :org, :engagement, 'Assistant', 'Test', 'Owner', 'Test', '{}')"),
            {"id": ai_system_id, "org": org_id, "engagement": engagement_id},
        )
    app.dependency_overrides[require_tenant] = lambda: TenantIdentity(
        org_id=org_id, user_id="user_test", provider_org_id="org_test"
    )
    client = TestClient(app)
    try:
        rejected = client.post(
            "/api/risks",
            json={"title": "Unknown AI", "description": "Invalid link", "likelihood": 1, "impact": 1, "ai_system_id": str(uuid4())},
        )
        assert rejected.status_code == 404
        created = client.post(
            "/api/risks",
            json={
                "title": "Credential compromise",
                "description": "Administrator credentials may be compromised.",
                "likelihood": 3,
                "impact": 5,
                "control_ids": ["IA-2"],
                "ai_system_id": str(ai_system_id),
            },
        )
        assert created.status_code == 201
        risk_id = created.json()["id"]
        assert client.get("/api/risks").json()[0]["ai_system_id"] == str(ai_system_id)
        with engine.begin() as connection:
            connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
            connection.execute(text("DELETE FROM ai_systems WHERE id = :id"), {"id": ai_system_id})
        assert client.get("/api/risks").json()[0]["ai_system_id"] is None
        assert client.patch(
            f"/api/risks/{risk_id}/status", json={"status": "mitigating"}
        ).status_code == 204
        assert client.delete(f"/api/risks/{risk_id}").status_code == 204
    finally:
        app.dependency_overrides.clear()
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)}
            )
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
