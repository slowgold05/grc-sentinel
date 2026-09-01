from datetime import date
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
    exchange_act_reporting_company: bool | None = None
    sox_filer_category: Literal[
        "large_accelerated_filer",
        "accelerated_filer",
        "non_accelerated_filer",
        "emerging_growth_company",
        "newly_public_transition",
        "registered_investment_company",
        "asset_backed_issuer",
        "private_company",
        "not_determined",
    ] | None = None
    sox_reporting_period_end: date | None = None
    sox_management_icfr_assessment_required: bool | None = None
    sox_auditor_attestation_required: bool | None = None
    sox_management_assessment_status: Literal[
        "effective", "ineffective", "not_completed", "not_determined"
    ] | None = None
    sox_attestation_status: Literal[
        "unqualified", "adverse", "disclaimer", "not_required", "not_completed", "not_determined"
    ] | None = None
    sox_scope_confirmed: bool | None = None
    eu_financial_entity: bool | None = None
    dora_entity_type: Literal[
        "credit_institution",
        "payment_institution",
        "account_information_service_provider",
        "electronic_money_institution",
        "investment_firm",
        "crypto_asset_service_provider",
        "central_securities_depository",
        "central_counterparty",
        "trading_venue",
        "trade_repository",
        "fund_manager",
        "data_reporting_service_provider",
        "insurance_entity",
        "insurance_intermediary",
        "occupational_pension_institution",
        "credit_rating_agency",
        "critical_benchmark_administrator",
        "crowdfunding_service_provider",
        "securitisation_repository",
        "other_article_2_entity",
    ] | None = None
    dora_eu_operating_nexus: bool | None = None
    dora_article_2_exclusion: Literal[
        "none",
        "small_alternative_investment_fund_manager",
        "small_insurance_or_reinsurance_undertaking",
        "small_occupational_pension_institution",
        "mifid_exempt_person",
        "micro_or_small_insurance_intermediary",
        "post_office_giro_institution",
        "member_state_excluded_credit_institution",
        "other",
        "not_determined",
    ] | None = None
    dora_group_context: bool | None = None
    dora_ict_third_party_provider: bool | None = None
    dora_critical_ict_provider_designated: bool | None = None
    dora_scope_confirmed: bool | None = None
    california_consumer_data: bool | None = None
    ccpa_covered_business: bool | None = None
    ccpa_for_profit: bool | None = None
    ccpa_does_business_in_california: bool | None = None
    ccpa_determines_processing_purposes: bool | None = None
    ccpa_threshold_year: int | None = Field(default=None, ge=2020, le=2100)
    ccpa_gross_revenue_usd: int | None = Field(default=None, ge=0)
    ccpa_consumers_or_households: int | None = Field(default=None, ge=0)
    ccpa_selling_sharing_revenue_percent: float | None = Field(default=None, ge=0, le=100)
    ccpa_related_entity: bool | None = None
    ccpa_exemption: Literal[
        "none",
        "glba_information",
        "cfipa_information",
        "hipaa_phi",
        "nonprofit",
        "government_entity",
        "other",
        "not_determined",
    ] | None = None
    mas_trm_notice_subject: bool | None = None
    mas_institution_type: Literal[
        "licensed_insurer_or_insurance_agent",
        "bank",
        "credit_or_charge_card_issuer",
        "finance_company",
        "merchant_bank",
        "payment_or_dpt_entity",
        "money_broker",
        "licensed_credit_bureau",
        "registered_insurance_broker",
        "capital_markets_financial_institution",
        "licensed_financial_adviser",
        "licensed_trust_company",
    ] | None = None
    mas_trm_notice_number: Literal[
        "FSM-N03",
        "FSM-N05",
        "FSM-N07",
        "FSM-N09",
        "FSM-N11",
        "FSM-N13",
        "FSM-N15",
        "FSM-N17",
        "FSM-N19",
        "FSM-N21",
        "FSM-N23",
        "FSM-N25",
    ] | None = None
    mas_licence_or_approval_confirmed: bool | None = None
    mas_legacy_notice_transition_complete: bool | None = None
    mas_customer_information_handled: bool | None = None
    mas_critical_system_framework_established: bool | None = None
    mas_critical_systems_identified: bool | None = None
    mas_scope_confirmed: bool | None = None

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, value: str) -> str:
        """Store domains in their validated canonical form."""
        return normalize_domain(value)

    @field_validator("geos", "data_types", "cloud_providers")
    @classmethod
    def normalize_fact_lists(cls, values: list[str]) -> list[str]:
        return sorted({value.strip().lower() for value in values if value.strip()})
