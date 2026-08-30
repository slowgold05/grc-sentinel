from pathlib import Path

from ruleset.rules.loader import load_rules


def test_loads_versioned_hipaa_ruleset() -> None:
    path = Path(__file__).parents[2] / "src/ruleset/rules/rulesets/hipaa-v2.json"
    rules = load_rules(path)
    assert [(rule.rule_id, rule.version) for rule in rules] == [("hipaa-covered-entity-v2", 2)]
