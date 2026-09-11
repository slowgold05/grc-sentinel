import json
from pathlib import Path
from uuid import uuid4

from ruleset.ai_governance.dogfood import build_dogfood_report
from ruleset.database import engine


def test_dogfood_report_is_reproducible_and_blocks_regressions() -> None:
    """Run real guardrails and emit a stable machine-readable report."""
    report = build_dogfood_report(
        engine,
        org_a=uuid4(),
        org_b=uuid4(),
        engagement_id=uuid4(),
    )
    payload = report.model_dump(mode="json") | {"passed": report.passed}
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    assert report.passed, rendered
    assert len(report.checks) == 9
    assert "do not establish broad model safety" in report.disclaimer
    assert json.loads(rendered)["fixture_version"] == "grc-sentinel-fictional-v1"
    expected = Path(__file__).with_name("dogfood-report.json")
    assert payload == json.loads(expected.read_text(encoding="utf-8"))
