from datetime import UTC, datetime

from ruleset.monitoring.models import ControlTest, TestResult as ControlTestResult


class PassingTest:
    test_id = "github-org-mfa-v1"
    control_ids = ["IA-2", "CC6.1"]

    def run(self, connection: object) -> ControlTestResult:
        return ControlTestResult(
            status="pass",
            observed={"two_factor_requirement_enabled": True},
            tested_at=datetime.now(UTC),
        )


def test_control_test_contract() -> None:
    test = PassingTest()

    assert isinstance(test, ControlTest)
    assert test.run(object()).status == "pass"
