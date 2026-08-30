from ruleset.generation.models import GeneratedStatement, GenerationOutput, RetrievedControl
from ruleset.generation.verify import verify_control_citations


def test_rejects_control_ids_outside_retrieval_context() -> None:
    output = GenerationOutput(
        statements=[
            GeneratedStatement(
                text="Administrators must use MFA.",
                control_ids=["IA-2", "FAKE-9"],
            )
        ]
    )
    verdict = verify_control_citations(
        output, [RetrievedControl(control_id="IA-2", text="Require authentication.")]
    )
    assert not verdict.accepted
    assert verdict.invalid_control_ids == ["FAKE-9"]
