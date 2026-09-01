from ruleset.intake.models import CompanyIntake


def intake(**facts: object) -> CompanyIntake:
    """Build a fictional California privacy intake."""
    return CompanyIntake(
        company_name="California Fintech",
        domain="example.com",
        employee_count=40,
        **facts,
    )


def test_ccpa_records_threshold_values_with_their_period() -> None:
    result = intake(
        ccpa_for_profit=True,
        ccpa_does_business_in_california=True,
        ccpa_determines_processing_purposes=True,
        california_consumer_data=True,
        ccpa_threshold_year=2025,
        ccpa_gross_revenue_usd=26_625_000,
        ccpa_consumers_or_households=100_000,
        ccpa_selling_sharing_revenue_percent=50,
        ccpa_exemption="none",
    )

    assert result.ccpa_threshold_year == 2025
    assert result.ccpa_gross_revenue_usd == 26_625_000


def test_glba_exemption_is_information_specific_not_entity_wide() -> None:
    result = intake(
        ccpa_covered_business=True,
        california_consumer_data=True,
        ccpa_exemption="glba_information",
    )

    assert result.ccpa_covered_business is True
    assert result.ccpa_exemption == "glba_information"


def test_related_entity_status_is_preserved_separately() -> None:
    result = intake(
        ccpa_covered_business=True,
        ccpa_related_entity=True,
        california_consumer_data=True,
    )

    assert result.ccpa_related_entity is True
