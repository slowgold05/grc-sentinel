from uuid import UUID

from sqlalchemy import Engine, text

from ruleset.generation.faithfulness import FaithfulnessVerdict
from ruleset.generation.models import CitationVerdict, GenerationOutput


def store_policy(
    engine: Engine,
    org_id: UUID,
    engagement_id: UUID,
    policy_type: str,
    section: str,
    output: GenerationOutput,
    citations: CitationVerdict,
    faithfulness: list[FaithfulnessVerdict],
) -> UUID:
    """Atomically store policy statements only after deterministic citation acceptance."""
    if not citations.accepted:
        raise ValueError("policy with invalid control citations cannot be stored")
    if len(faithfulness) != len(output.statements):
        raise ValueError("every statement requires a faithfulness verdict")
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        policy_id = connection.execute(
            text(
                "INSERT INTO policies (org_id, engagement_id, policy_type) "
                "VALUES (:org_id, :engagement_id, :policy_type) RETURNING id"
            ),
            {"org_id": org_id, "engagement_id": engagement_id, "policy_type": policy_type},
        ).scalar_one()
        for sequence, (statement, verdict) in enumerate(
            zip(output.statements, faithfulness, strict=True), start=1
        ):
            connection.execute(
                text(
                    "INSERT INTO statements (org_id, policy_id, section, seq, text, control_ids, "
                    "parameters_used, faithful, verification_issue) VALUES (:org_id, :policy_id, "
                    ":section, :seq, :text, :control_ids, :parameters, :faithful, :issue)"
                ),
                {
                    "org_id": org_id,
                    "policy_id": policy_id,
                    "section": section,
                    "seq": sequence,
                    "text": statement.text,
                    "control_ids": statement.control_ids,
                    "parameters": statement.parameters_used,
                    "faithful": verdict.faithful,
                    "issue": verdict.issue,
                },
            )
    return policy_id


def record_model_usage(
    engine: Engine,
    org_id: UUID,
    engagement_id: UUID,
    *,
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost_microusd: int,
) -> None:
    """Append one provider-reported usage record for engagement cost accounting."""
    if min(input_tokens, output_tokens, cost_microusd) < 0:
        raise ValueError("usage values cannot be negative")
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        connection.execute(
            text(
                "INSERT INTO model_usage (org_id, engagement_id, provider, model, input_tokens, "
                "output_tokens, cost_microusd) VALUES (:org_id, :engagement_id, :provider, :model, "
                ":input_tokens, :output_tokens, :cost_microusd)"
            ),
            {
                "org_id": org_id,
                "engagement_id": engagement_id,
                "provider": provider,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_microusd": cost_microusd,
            },
        )
