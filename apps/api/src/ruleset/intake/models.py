from typing import Literal

from pydantic import BaseModel, Field, field_validator

from ruleset.osint.dns_posture import normalize_domain


class CompanyIntake(BaseModel):
    """Validated company facts collected by the intake wizard."""

    company_name: str = Field(min_length=1, max_length=200)
    domain: str
    employee_count: int = Field(ge=1)
    geos: list[str] = Field(default_factory=list)
    data_types: list[str] = Field(default_factory=list)
    sends_external_email: bool | None = None
    cloud_providers: list[str] = Field(default_factory=list)
    financial_services: bool = False
    ftc_financial_institution: bool | None = None
    handles_customer_financial_information: bool | None = None
    glba_section_505_other_regulator: bool | None = None
    glba_customer_count: int | None = Field(default=None, ge=0)
    glba_financial_activity: Literal[
        "mortgage_lending",
        "payday_lending",
        "finance_company",
        "mortgage_broker",
        "account_servicing",
        "check_cashing",
        "wire_transfer",
        "collection_agency",
        "credit_counseling_or_financial_advice",
        "tax_preparation",
        "non_federally_insured_credit_union",
        "non_sec_registered_investment_adviser",
        "finder",
        "other_financial_activity",
    ] | None = None
    handles_cardholder_data: bool = False
    pci_entity_role: Literal[
        "merchant", "service_provider", "merchant_and_service_provider", "other"
    ] | None = None
    pci_stores_account_data: bool | None = None
    pci_processes_account_data: bool | None = None
    pci_transmits_account_data: bool | None = None
    pci_can_impact_cde: bool | None = None
    pci_fully_outsourced: bool | None = None
    pci_cde_scope_confirmed: bool | None = None
    pci_validation_method: Literal[
        "saq_a",
        "saq_a_ep",
        "saq_b",
        "saq_b_ip",
        "saq_c",
        "saq_c_vt",
        "saq_d_merchant",
        "saq_d_service_provider",
        "roc",
        "not_determined",
    ] | None = None
    sec_regulated: bool = False
    reg_sp_covered_institution: bool | None = None
    reg_sp_entity_type: Literal[
        "broker_dealer",
        "investment_company",
        "registered_investment_adviser",
        "funding_portal",
        "transfer_agent",
        "other",
    ] | None = None
    reg_sp_size_cohort: Literal["larger", "smaller", "not_determined"] | None = None
    reg_sp_customer_information: bool | None = None
    reg_sp_service_provider_used: bool | None = None
    finra_member: bool | None = None
    finra_firm_type: Literal["carrying_clearing", "introducing", "other"] | None = None
    finra_customer_accounts: bool | None = None
    finra_mission_critical_systems_identified: bool | None = None
    finra_bcp_scope_confirmed: bool | None = None
    nydfs_licensed: bool | None = None
    nydfs_authorization_type: Literal[
        "banking", "insurance", "financial_services", "virtual_currency", "other"
    ] | None = None
    nydfs_exemption: Literal[
        "none", "500.19(a)", "500.19(b)", "500.19(c)", "500.19(d)", "500.19(e)", "not_determined"
    ] | None = None
    nydfs_class_a_company: bool | None = None
    nydfs_uses_affiliate_program: bool | None = None
    public_company: bool = False
    exchange_act_reporting_company: bool = False
    eu_financial_entity: bool = False
    california_consumer_data: bool = False
    ccpa_covered_business: bool = False
    mas_trm_notice_subject: bool = False

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, value: str) -> str:
        """Store domains in their validated canonical form."""
        return normalize_domain(value)

    @field_validator("geos", "data_types", "cloud_providers")
    @classmethod
    def normalize_fact_lists(cls, values: list[str]) -> list[str]:
        return sorted({value.strip().lower() for value in values if value.strip()})
