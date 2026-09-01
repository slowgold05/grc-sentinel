from ruleset.intake.models import CompanyIntake


def intake(**facts: object) -> CompanyIntake:
    """Build a fictional DORA intake."""
    return CompanyIntake(
        company_name="EU Fintech",
        domain="example.com",
        employee_count=40,
        **facts,
    )


def test_dora_preserves_article_2_category_and_exclusion() -> None:
    result = intake(
        eu_financial_entity=True,
        dora_entity_type="payment_institution",
        dora_eu_operating_nexus=True,
        dora_article_2_exclusion="none",
        dora_scope_confirmed=True,
    )

    assert result.dora_entity_type == "payment_institution"
    assert result.dora_article_2_exclusion == "none"


def test_ict_provider_role_does_not_imply_financial_entity_scope() -> None:
    result = intake(
        eu_financial_entity=False,
        dora_ict_third_party_provider=True,
        dora_critical_ict_provider_designated=False,
    )

    assert result.eu_financial_entity is False
    assert result.dora_ict_third_party_provider is True


def test_critical_provider_designation_is_recorded_separately() -> None:
    result = intake(
        dora_ict_third_party_provider=True,
        dora_critical_ict_provider_designated=True,
        dora_group_context=True,
    )

    assert result.dora_critical_ict_provider_designated is True
    assert result.dora_group_context is True
