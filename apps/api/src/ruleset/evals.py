from pydantic import BaseModel

from ruleset.generation.models import GenerationOutput, RetrievedControl
from ruleset.generation.verify import verify_control_citations
from ruleset.rules.engine import evaluate
from ruleset.rules.models import CompanyFacts, Rule


class ApplicabilityCase(BaseModel):
    """Expert-labeled company facts and expected applicable regulations."""

    case_id: str
    facts: CompanyFacts
    expected_regulations: set[str]


class ApplicabilityMetrics(BaseModel):
    """Aggregate deterministic applicability quality metrics."""

    precision: float
    recall: float
    true_positives: int
    false_positives: int
    false_negatives: int


def score_applicability(cases: list[ApplicabilityCase], rules: list[Rule]) -> ApplicabilityMetrics:
    """Calculate micro-averaged applicability precision and recall."""
    true_positives = false_positives = false_negatives = 0
    for case in cases:
        actual = {item.regulation for item in evaluate(case.facts, rules)}
        true_positives += len(actual & case.expected_regulations)
        false_positives += len(actual - case.expected_regulations)
        false_negatives += len(case.expected_regulations - actual)
    return ApplicabilityMetrics(
        precision=true_positives / (true_positives + false_positives)
        if true_positives + false_positives
        else 1.0,
        recall=true_positives / (true_positives + false_negatives)
        if true_positives + false_negatives
        else 1.0,
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
    )


def citation_validity_rate(
    samples: list[tuple[GenerationOutput, list[RetrievedControl]]],
) -> float:
    """Return the fraction of generated samples with only retrieved control IDs."""
    if not samples:
        return 1.0
    return sum(verify_control_citations(output, controls).accepted for output, controls in samples) / len(samples)
