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
                    "ftc_financial_institution": True,
                    "handles_customer_financial_information": True,
                    "glba_section_505_other_regulator": False,
                    "glba_customer_count": 12000,
                    "glba_financial_activity": "finance_company",
                    "handles_cardholder_data": True,
                    "reg_sp_covered_institution": True,
                    "finra_member": True,
                    "nydfs_licensed": True,
                    "exchange_act_reporting_company": True,
                    "eu_financial_entity": True,
                    "ccpa_covered_business": True,
                    "mas_trm_notice_subject": True,
                },
                "assurance_objectives": [
                    {
                        "framework": "SOC 2 TSC",
                        "basis": "customer_contract",
                        "scope": "Security criteria for enterprise procurement",
                    },
                    {
                        "framework": "ISO 27001",
                        "basis": "company_strategy",
                    },
                    {
                        "framework": "PCI DSS",
                        "basis": "customer_contract",
                        "scope": "Cardholder data environment",
                    },
                ],
            },
        )
        assert response.status_code == 201
        assert response.json()["determinations"][0]["regulation"] == "HIPAA"
        assert [item["framework"] for item in response.json()["assurance_objectives"]] == [
            "SOC 2 TSC",
            "ISO 27001",
            "PCI DSS",
        ]
        engagement_id = response.json()["id"]
        summary = TestClient(app).get("/api/engagements").json()[0]
        assert summary["regulations"] == ["HIPAA"]
        assert summary["company"]["mas_trm_notice_subject"] is True
        assert summary["company"]["reg_sp_covered_institution"] is True
        assert summary["company"]["glba_customer_count"] == 12000
        assert summary["company"]["glba_financial_activity"] == "finance_company"
        assert {item["framework"] for item in summary["assurance_objectives"]} == {
            "ISO 27001",
            "PCI DSS",
            "SOC 2 TSC",
        }
        readiness = TestClient(app).get(
            f"/api/engagements/{engagement_id}/assurance-readiness"
        ).json()
        assert {item["framework"] for item in readiness} == {
            "ISO 27001",
            "PCI DSS",
            "SOC 2 TSC",
        }
        assert all(item["total"] > 0 and item["not_assessed"] == item["total"] for item in readiness)
        assert TestClient(app).delete(f"/api/engagements/{engagement_id}").status_code == 204
    finally:
        app.dependency_overrides.clear()
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)}
            )
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
