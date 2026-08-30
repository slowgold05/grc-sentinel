from io import BytesIO

from openpyxl import Workbook

from ruleset.kb.ingest_scf import parse_scf


def test_parses_ten_known_mappings() -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "SCF 2026.2"
    sheet.append(
        [
            "SCF Control",
            "SCF #",
            "Secure Controls Framework (SCF)\nControl Description",
            "AICPA\nTSC 2017:2022 (used for SOC 2)",
            "ISO\n27001\n2022",
            "NIST\n800-53\nR5",
            "PCI DSS\n4.0.1",
            "US\nHIPAA\nSecurity Rule / NIST SP 800-66 R2",
        ]
    )
    sheet.append(
        [
            "Governance",
            "GOV-01",
            "Govern the security program.",
            "CC1.1\nCC1.2",
            "4.4\n5.1",
            "PM-01\nPM-02",
            "12.4\nA3.1.2",
            "§ 164.306(a)(1)\n§ 164.316(a)",
        ]
    )
    payload = BytesIO()
    workbook.save(payload)

    control = parse_scf(payload.getvalue())[0]

    assert control.control_code == "GOV-01"
    assert len(control.mappings) == 10
    assert {mapping.control_code for mapping in control.mappings} >= {"PM-1", "CC1.1", "4.4"}
