from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import text

from ruleset.auth import TenantIdentity, require_tenant
from ruleset.database import engine
from ruleset.main import app


def test_intake_creates_engagement_and_hipaa_determination() -> None:
    org_id = uuid4()
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        connection.execute(
            text("INSERT INTO orgs (id, name) VALUES (:id, 'intake api test')"), {"id": org_id}
        )
    app.dependency_overrides[require_tenant] = lambda: TenantIdentity(
        org_id=org_id, user_id="user_test", provider_org_id="org_test"
    )
    try:
        response = TestClient(app).post(
            "/api/engagements",
            json={
                "company": {
                    "company_name": "Example Health",
                    "domain": "example.com",
                    "employee_count": 20,
                    "geos": ["US"],
                    "data_types": ["PHI"],
                }
            },
        )
        assert response.status_code == 201
        assert response.json()["determinations"][0]["regulation"] == "HIPAA"
    finally:
        app.dependency_overrides.clear()
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)}
            )
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
