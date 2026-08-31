from uuid import uuid4

from fastapi.testclient import TestClient

from ruleset.auth import TenantIdentity, require_tenant
from ruleset.main import app


def test_coverage_analysis_rejects_an_upload_outside_the_engagement() -> None:
    app.dependency_overrides[require_tenant] = lambda: TenantIdentity(
        org_id=uuid4(), user_id="test-user", provider_org_id="org_test"
    )
    try:
        response = TestClient(app).post(f"/api/engagements/{uuid4()}/uploads/{uuid4()}/analyze")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
