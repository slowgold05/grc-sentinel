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
                    "pci_entity_role": "merchant",
                    "pci_stores_account_data": True,
                    "pci_processes_account_data": True,
                    "pci_transmits_account_data": True,
                    "pci_can_impact_cde": True,
                    "pci_fully_outsourced": False,
                    "pci_cde_scope_confirmed": True,
                    "pci_validation_method": "saq_d_merchant",
                    "reg_sp_covered_institution": True,
                    "reg_sp_entity_type": "broker_dealer",
                    "reg_sp_size_cohort": "larger",
                    "reg_sp_customer_information": True,
                    "reg_sp_service_provider_used": True,
                    "finra_member": True,
                    "finra_firm_type": "carrying_clearing",
                    "finra_customer_accounts": True,
                    "finra_mission_critical_systems_identified": True,
                    "finra_bcp_scope_confirmed": True,
                    "nydfs_licensed": True,
                    "nydfs_authorization_type": "financial_services",
                    "nydfs_exemption": "none",
                    "nydfs_class_a_company": False,
                    "nydfs_uses_affiliate_program": False,
                    "exchange_act_reporting_company": True,
                    "eu_financial_entity": True,
                    "ccpa_covered_business": True,
                    "california_consumer_data": True,
                    "ccpa_for_profit": True,
                    "ccpa_does_business_in_california": True,
                    "ccpa_determines_processing_purposes": True,
                    "ccpa_threshold_year": 2025,
                    "ccpa_gross_revenue_usd": 30000000,
                    "ccpa_consumers_or_households": 120000,
                    "ccpa_selling_sharing_revenue_percent": 10,
                    "ccpa_related_entity": False,
                    "ccpa_exemption": "none",
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
        assert summary["company"]["pci_entity_role"] == "merchant"
        assert summary["company"]["pci_validation_method"] == "saq_d_merchant"
        assert summary["company"]["reg_sp_entity_type"] == "broker_dealer"
        assert summary["company"]["finra_firm_type"] == "carrying_clearing"
        assert summary["company"]["nydfs_exemption"] == "none"
        assert summary["company"]["ccpa_threshold_year"] == 2025
        assert summary["company"]["ccpa_exemption"] == "none"
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
