from collections.abc import Iterable

from ruleset.generation.models import CitationVerdict, GenerationOutput, RetrievedControl


def invalid_citations(cited: Iterable[str], allowed: Iterable[str]) -> list[str]:
    """Return sorted citation IDs that were not in retrieval context."""
    return sorted(set(cited) - set(allowed))


def verify_control_citations(
    output: GenerationOutput, retrieved: list[RetrievedControl]
) -> CitationVerdict:
    """Reject every generated control ID absent from the retrieval context."""
    invalid = invalid_citations(
        (control_id for statement in output.statements for control_id in statement.control_ids),
        (control.control_id for control in retrieved),
    )
    return CitationVerdict(accepted=not invalid, invalid_control_ids=invalid)
