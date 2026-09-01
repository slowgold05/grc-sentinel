from datetime import date

from ruleset.intake.models import CompanyIntake


def intake(**facts: object) -> CompanyIntake:
    """Build a fictional SOX ICFR intake."""
    return CompanyIntake(
        company_name="US Reporting Company",
        domain="example.com",
        employee_count=100,
        **facts,
    )


def test_sox_preserves_filer_category_and_reporting_period() -> None:
    result = intake(
        exchange_act_reporting_company=True,
        sox_filer_category="accelerated_filer",
        sox_reporting_period_end=date(2025, 12, 31),
        sox_management_icfr_assessment_required=True,
        sox_auditor_attestation_required=True,
    )

    assert result.sox_filer_category == "accelerated_filer"
    assert result.sox_reporting_period_end == date(2025, 12, 31)


def test_egc_attestation_exemption_does_not_remove_management_assessment() -> None:
    result = intake(
        exchange_act_reporting_company=True,
        sox_filer_category="emerging_growth_company",
        sox_management_icfr_assessment_required=True,
        sox_auditor_attestation_required=False,
        sox_attestation_status="not_required",
    )

    assert result.sox_management_icfr_assessment_required is True
    assert result.sox_auditor_attestation_required is False


def test_private_company_is_explicitly_outside_reporting_objective() -> None:
    result = intake(
        exchange_act_reporting_company=False,
        sox_filer_category="private_company",
        sox_management_icfr_assessment_required=False,
        sox_scope_confirmed=True,
    )

    assert result.exchange_act_reporting_company is False
    assert result.sox_filer_category == "private_company"
