from ruleset.intake.models import CompanyIntake


def intake(**facts: object) -> CompanyIntake:
    """Build a fictional MAS TRM intake."""
    return CompanyIntake(
        company_name="Singapore Fintech",
        domain="example.com",
        employee_count=40,
        **facts,
    )


def test_mas_trm_preserves_institution_and_exact_notice() -> None:
    result = intake(
        mas_trm_notice_subject=True,
        mas_institution_type="payment_or_dpt_entity",
        mas_trm_notice_number="FSM-N13",
        mas_licence_or_approval_confirmed=True,
        mas_scope_confirmed=True,
    )

    assert result.mas_institution_type == "payment_or_dpt_entity"
    assert result.mas_trm_notice_number == "FSM-N13"


def test_no_critical_systems_does_not_erase_framework_fact() -> None:
    result = intake(
        mas_critical_system_framework_established=True,
        mas_critical_systems_identified=False,
    )

    assert result.mas_critical_system_framework_established is True
    assert result.mas_critical_systems_identified is False


def test_current_notice_transition_is_explicit() -> None:
    result = intake(
        mas_trm_notice_subject=True,
        mas_trm_notice_number="FSM-N05",
        mas_legacy_notice_transition_complete=False,
    )

    assert result.mas_legacy_notice_transition_complete is False
