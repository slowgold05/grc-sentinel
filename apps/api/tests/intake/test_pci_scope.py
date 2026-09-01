from ruleset.intake.models import CompanyIntake


def test_service_provider_scope_does_not_require_direct_account_data_handling() -> None:
    intake = CompanyIntake(
        company_name="CDE Security Provider",
        domain="example.com",
        employee_count=50,
        pci_entity_role="service_provider",
        pci_stores_account_data=False,
        pci_processes_account_data=False,
        pci_transmits_account_data=False,
        pci_can_impact_cde=True,
        pci_fully_outsourced=False,
        pci_cde_scope_confirmed=True,
        pci_validation_method="saq_d_service_provider",
    )

    assert intake.pci_can_impact_cde is True
    assert intake.handles_cardholder_data is False


def test_outsourced_merchant_retains_explicit_validation_scope() -> None:
    intake = CompanyIntake(
        company_name="Redirect Merchant",
        domain="example.com",
        employee_count=10,
        pci_entity_role="merchant",
        pci_stores_account_data=False,
        pci_processes_account_data=False,
        pci_transmits_account_data=False,
        pci_can_impact_cde=True,
        pci_fully_outsourced=True,
        pci_cde_scope_confirmed=True,
        pci_validation_method="saq_a",
    )

    assert intake.pci_fully_outsourced is True
    assert intake.pci_validation_method == "saq_a"
