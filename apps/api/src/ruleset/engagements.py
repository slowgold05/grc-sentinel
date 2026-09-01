from datetime import UTC, date, datetime, timedelta
import json
from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Engine, text

from ruleset.intake.models import CompanyIntake
from ruleset.rules.engine import evaluate
from ruleset.rules.loader import load_rules
from ruleset.rules.models import CompanyFacts, Determination
from ruleset.rules.store import insert_determinations

_HIPAA_RULES = Path(__file__).parent / "rules" / "rulesets" / "hipaa-v2.json"


class AssuranceObjectiveCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    framework: Literal["ISO 27001", "SOC 2 TSC", "NIST SP 800-53", "PCI DSS"]
    basis: Literal["customer_contract", "company_strategy", "regulator_request"]
    target_date: date | None = None
    scope: str = Field(default="", max_length=500)


class EngagementCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company: CompanyIntake
    retention_days: int = Field(default=90, ge=1, le=365)
    assurance_objectives: list[AssuranceObjectiveCreate] = Field(default_factory=list, max_length=4)


class AssuranceObjective(BaseModel):
    framework: str
    version: str
    basis: str
    target_date: date | None
    scope: str


class AssuranceReadiness(BaseModel):
    framework: str
    version: str
    total: int
    covered: int
    partial: int
    missing: int
    not_assessed: int


class EngagementCreated(BaseModel):
    id: UUID
    determinations: list[Determination]
    assurance_objectives: list[AssuranceObjective]


class EngagementSummary(BaseModel):
    id: UUID
    company: CompanyIntake
    created_at: datetime
    expires_at: datetime
    regulations: list[str]
    assurance_objectives: list[AssuranceObjective]


def create_engagement(
    engine: Engine, org_id: UUID, selected_by: str, request: EngagementCreate
) -> EngagementCreated:
    """Create an engagement and persist deterministic applicability evidence."""
    facts = CompanyFacts(
        {
            "employee_count": request.company.employee_count,
            "geos": request.company.geos,
            "data_types": request.company.data_types,
            "sends_external_email": request.company.sends_external_email,
            "cloud_providers": request.company.cloud_providers,
            "financial_services": request.company.financial_services,
            "ftc_financial_institution": request.company.ftc_financial_institution,
            "handles_customer_financial_information": (
                request.company.handles_customer_financial_information
            ),
            "glba_section_505_other_regulator": (
                request.company.glba_section_505_other_regulator
            ),
            "glba_customer_count": request.company.glba_customer_count,
            "glba_financial_activity": request.company.glba_financial_activity,
            "handles_cardholder_data": request.company.handles_cardholder_data,
            "pci_entity_role": request.company.pci_entity_role,
            "pci_stores_account_data": request.company.pci_stores_account_data,
            "pci_processes_account_data": request.company.pci_processes_account_data,
            "pci_transmits_account_data": request.company.pci_transmits_account_data,
            "pci_can_impact_cde": request.company.pci_can_impact_cde,
            "pci_fully_outsourced": request.company.pci_fully_outsourced,
            "pci_cde_scope_confirmed": request.company.pci_cde_scope_confirmed,
            "pci_validation_method": request.company.pci_validation_method,
            "sec_regulated": request.company.sec_regulated,
            "reg_sp_covered_institution": request.company.reg_sp_covered_institution,
            "reg_sp_entity_type": request.company.reg_sp_entity_type,
            "reg_sp_size_cohort": request.company.reg_sp_size_cohort,
            "reg_sp_customer_information": request.company.reg_sp_customer_information,
            "reg_sp_service_provider_used": request.company.reg_sp_service_provider_used,
            "finra_member": request.company.finra_member,
            "finra_firm_type": request.company.finra_firm_type,
            "finra_customer_accounts": request.company.finra_customer_accounts,
            "finra_mission_critical_systems_identified": (
                request.company.finra_mission_critical_systems_identified
            ),
            "finra_bcp_scope_confirmed": request.company.finra_bcp_scope_confirmed,
            "nydfs_licensed": request.company.nydfs_licensed,
            "nydfs_authorization_type": request.company.nydfs_authorization_type,
            "nydfs_exemption": request.company.nydfs_exemption,
            "nydfs_class_a_company": request.company.nydfs_class_a_company,
            "nydfs_uses_affiliate_program": request.company.nydfs_uses_affiliate_program,
            "public_company": request.company.public_company,
            "exchange_act_reporting_company": (
                request.company.exchange_act_reporting_company
            ),
            "eu_financial_entity": request.company.eu_financial_entity,
            "dora_entity_type": request.company.dora_entity_type,
            "dora_eu_operating_nexus": request.company.dora_eu_operating_nexus,
            "dora_article_2_exclusion": request.company.dora_article_2_exclusion,
            "dora_group_context": request.company.dora_group_context,
            "dora_ict_third_party_provider": request.company.dora_ict_third_party_provider,
            "dora_critical_ict_provider_designated": (
                request.company.dora_critical_ict_provider_designated
            ),
            "dora_scope_confirmed": request.company.dora_scope_confirmed,
            "california_consumer_data": request.company.california_consumer_data,
            "ccpa_covered_business": request.company.ccpa_covered_business,
            "ccpa_for_profit": request.company.ccpa_for_profit,
            "ccpa_does_business_in_california": (
                request.company.ccpa_does_business_in_california
            ),
            "ccpa_determines_processing_purposes": (
                request.company.ccpa_determines_processing_purposes
            ),
            "ccpa_threshold_year": request.company.ccpa_threshold_year,
            "ccpa_gross_revenue_usd": request.company.ccpa_gross_revenue_usd,
            "ccpa_consumers_or_households": request.company.ccpa_consumers_or_households,
            "ccpa_selling_sharing_revenue_percent": (
                request.company.ccpa_selling_sharing_revenue_percent
            ),
            "ccpa_related_entity": request.company.ccpa_related_entity,
            "ccpa_exemption": request.company.ccpa_exemption,
            "mas_trm_notice_subject": request.company.mas_trm_notice_subject,
            "mas_institution_type": request.company.mas_institution_type,
            "mas_trm_notice_number": request.company.mas_trm_notice_number,
            "mas_licence_or_approval_confirmed": (
                request.company.mas_licence_or_approval_confirmed
            ),
            "mas_legacy_notice_transition_complete": (
                request.company.mas_legacy_notice_transition_complete
            ),
            "mas_customer_information_handled": (
                request.company.mas_customer_information_handled
            ),
            "mas_critical_system_framework_established": (
                request.company.mas_critical_system_framework_established
            ),
            "mas_critical_systems_identified": (
                request.company.mas_critical_systems_identified
            ),
            "mas_scope_confirmed": request.company.mas_scope_confirmed,
        }
    )
    determinations = evaluate(facts, load_rules(_HIPAA_RULES))
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        engagement_id = connection.execute(
            text(
                "INSERT INTO engagements (org_id, company, expires_at) "
                "VALUES (:org_id, CAST(:company AS jsonb), :expires_at) RETURNING id"
            ),
            {
                "org_id": org_id,
                "company": json.dumps(request.company.model_dump(mode="json")),
                "expires_at": datetime.now(UTC) + timedelta(days=request.retention_days),
            },
        ).scalar_one()
        insert_determinations(connection, org_id, engagement_id, determinations)
        objectives = []
        for objective in request.assurance_objectives:
            framework = connection.execute(
                text("SELECT id, version FROM frameworks WHERE name = :name"),
                {"name": objective.framework},
            ).mappings().one_or_none()
            if framework is None:
                raise ValueError(f"framework is not installed: {objective.framework}")
            connection.execute(
                text(
                    "INSERT INTO assurance_objectives "
                    "(org_id, engagement_id, framework_id, basis, target_date, scope, selected_by) "
                    "VALUES (:org_id, :engagement_id, :framework_id, :basis, :target_date, :scope, :selected_by)"
                ),
                {
                    "org_id": org_id,
                    "engagement_id": engagement_id,
                    "framework_id": framework["id"],
                    "basis": objective.basis,
                    "target_date": objective.target_date,
                    "scope": objective.scope,
                    "selected_by": selected_by,
                },
            )
            objectives.append(
                AssuranceObjective(
                    framework=objective.framework,
                    version=framework["version"],
                    basis=objective.basis,
                    target_date=objective.target_date,
                    scope=objective.scope,
                )
            )
    return EngagementCreated(
        id=engagement_id, determinations=determinations, assurance_objectives=objectives
    )


def list_engagements(engine: Engine, org_id: UUID) -> list[EngagementSummary]:
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        rows = connection.execute(
            text(
                "SELECT e.id, e.company, e.created_at, e.expires_at, "
                "COALESCE(array_agg(r.name) FILTER (WHERE r.name IS NOT NULL), '{}') AS regulations "
                "FROM engagements e LEFT JOIN determinations d ON d.engagement_id = e.id "
                "LEFT JOIN regulations r ON r.id = d.regulation_id "
                "GROUP BY e.id ORDER BY e.created_at DESC"
            )
        ).mappings()
        engagements = [EngagementSummary.model_validate({**row, "assurance_objectives": []}) for row in rows]
        objective_rows = connection.execute(
            text(
                "SELECT o.engagement_id, f.name AS framework, f.version, o.basis, "
                "o.target_date, o.scope FROM assurance_objectives o "
                "JOIN frameworks f ON f.id = o.framework_id ORDER BY f.name"
            )
        ).mappings()
        by_id = {engagement.id: engagement for engagement in engagements}
        for row in objective_rows:
            if row["engagement_id"] in by_id:
                by_id[row["engagement_id"]].assurance_objectives.append(
                    AssuranceObjective.model_validate(row)
                )
        return engagements


def get_assurance_readiness(
    engine: Engine, org_id: UUID, engagement_id: UUID
) -> list[AssuranceReadiness]:
    """Summarize direct or strongly equivalent evidence for selected frameworks."""
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        rows = connection.execute(
            text(
                "WITH objective_controls AS ("
                "SELECT f.name AS framework, f.version, c.id AS control_id "
                "FROM assurance_objectives o JOIN frameworks f ON f.id = o.framework_id "
                "JOIN controls c ON c.framework_id = f.id WHERE o.engagement_id = :engagement_id"
                "), latest_results AS ("
                "SELECT DISTINCT ON (control_id) control_id, status FROM coverage_results "
                "WHERE engagement_id = :engagement_id ORDER BY control_id, created_at DESC"
                "), ranked AS ("
                "SELECT oc.framework, oc.version, oc.control_id, "
                "COALESCE(max(CASE lr.status WHEN 'covered' THEN 3 WHEN 'partial' THEN 2 "
                "WHEN 'missing' THEN 1 ELSE 0 END), 0) AS rank FROM objective_controls oc "
                "LEFT JOIN latest_results lr ON lr.control_id = oc.control_id OR EXISTS ("
                "SELECT 1 FROM crosswalks x WHERE x.relation = 'equivalent' AND x.strength >= 0.9 "
                "AND ((x.control_a = oc.control_id AND x.control_b = lr.control_id) "
                "OR (x.control_b = oc.control_id AND x.control_a = lr.control_id))) "
                "GROUP BY oc.framework, oc.version, oc.control_id"
                ") SELECT framework, version, count(*) AS total, "
                "count(*) FILTER (WHERE rank = 3) AS covered, "
                "count(*) FILTER (WHERE rank = 2) AS partial, "
                "count(*) FILTER (WHERE rank = 1) AS missing, "
                "count(*) FILTER (WHERE rank = 0) AS not_assessed "
                "FROM ranked GROUP BY framework, version ORDER BY framework"
            ),
            {"engagement_id": engagement_id},
        ).mappings()
    return [AssuranceReadiness.model_validate(row) for row in rows]
