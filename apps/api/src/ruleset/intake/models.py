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
    sec_regulated: bool = False
    reg_sp_covered_institution: bool = False
    finra_member: bool = False
    nydfs_licensed: bool = False
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
