import json
from pathlib import Path

from pydantic import TypeAdapter

from ruleset.evals import ApplicabilityCase, citation_validity_rate, score_applicability
from ruleset.generation.models import GeneratedStatement, GenerationOutput, RetrievedControl
from ruleset.rules.loader import load_rules


def test_golden_applicability_and_citation_metrics() -> None:
    raw = json.loads(Path(__file__).with_name("applicability.json").read_text(encoding="utf-8"))
    cases = TypeAdapter(list[ApplicabilityCase]).validate_python(raw)
    rules_path = Path(__file__).parents[2] / "src/ruleset/rules/rulesets/hipaa-v2.json"
    metrics = score_applicability(cases, load_rules(rules_path))
    assert len(cases) == 30
    assert (metrics.precision, metrics.recall) == (1.0, 1.0)

    valid = GenerationOutput(
        statements=[GeneratedStatement(text="Use MFA.", control_ids=["IA-2"])]
    )
    invalid = GenerationOutput(
        statements=[GeneratedStatement(text="Use MFA.", control_ids=["FAKE-1"])]
    )
    controls = [RetrievedControl(control_id="IA-2", text="Require authentication.")]
    assert citation_validity_rate([(valid, controls), (invalid, controls)]) == 0.5
