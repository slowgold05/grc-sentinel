import json
from pathlib import Path


ROOT = Path(__file__).parents[4]


def test_every_fintech_regime_has_a_complete_activation_gate() -> None:
    """Prevent a fintech regime from bypassing source and reviewer gates."""
    path = ROOT / "docs" / "fintech-activation-manifest.json"
    regimes = json.loads(path.read_text())

    assert len(regimes) == 9
    assert {item["classification"] for item in regimes} == {
        "regulation",
        "sro_rule",
        "reporting_objective",
        "contractual_standard",
    }
    for item in regimes:
        assert item["activation_status"] == "awaiting_human_review"
        assert item["minimum_profiles"] >= 30
        assert (ROOT / item["source_review"]).is_file()
        assert "mappings" in item["required_approvals"]
        assert "golden_profiles" in item["required_approvals"]
        assert item["browser_gate"]
        if item["candidate_profiles"]:
            assert (ROOT / item["candidate_profiles"]).is_file()
