from ruleset.intake.models import CompanyIntake


def intake(**facts: object) -> CompanyIntake:
    """Build the minimum fictional intake for scope-model checks."""
    return CompanyIntake(
        company_name="Fictional Finance",
        domain="example.com",
        employee_count=50,
        **facts,
    )


def test_reg_sp_preserves_entity_type_and_compliance_cohort() -> None:
    result = intake(
        reg_sp_covered_institution=True,
        reg_sp_entity_type="registered_investment_adviser",
        reg_sp_size_cohort="smaller",
        reg_sp_customer_information=True,
        reg_sp_service_provider_used=True,
    )

    assert result.reg_sp_entity_type == "registered_investment_adviser"
    assert result.reg_sp_size_cohort == "smaller"


def test_finra_scope_separates_membership_from_bcp_readiness() -> None:
    result = intake(
        finra_member=True,
        finra_firm_type="introducing",
        finra_customer_accounts=True,
        finra_mission_critical_systems_identified=False,
        finra_bcp_scope_confirmed=False,
    )

    assert result.finra_member is True
    assert result.finra_bcp_scope_confirmed is False


def test_nydfs_exemption_does_not_erase_covered_entity_status() -> None:
    result = intake(
        nydfs_licensed=True,
        nydfs_authorization_type="virtual_currency",
        nydfs_exemption="500.19(a)",
        nydfs_class_a_company=False,
        nydfs_uses_affiliate_program=True,
    )

    assert result.nydfs_licensed is True
    assert result.nydfs_exemption == "500.19(a)"
