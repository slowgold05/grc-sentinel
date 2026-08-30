from uuid import UUID
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Engine, text

from ruleset.generation.faithfulness import FaithfulnessVerdict
from ruleset.generation.models import CitationVerdict, GeneratedStatement, GenerationOutput
from ruleset.generation.export_docx import export_policy_docx


class PolicySummary(BaseModel):
    id: UUID
    engagement_id: UUID
    policy_type: str
    version: int
    created_at: datetime


def list_policies(engine: Engine, org_id: UUID) -> list[PolicySummary]:
    """Return the tenant's newest generated policies."""
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        rows = connection.execute(
            text(
                "SELECT id, engagement_id, policy_type, version, created_at FROM policies "
                "ORDER BY created_at DESC LIMIT 100"
            )
        ).mappings()
    return [PolicySummary.model_validate(row) for row in rows]


def export_stored_policy(engine: Engine, org_id: UUID, policy_id: UUID) -> tuple[str, bytes]:
    """Export a verified stored policy with its traceability appendix."""
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        policy = connection.execute(
            text(
                "SELECT p.policy_type, p.version, p.created_at, e.company FROM policies p "
                "JOIN engagements e ON e.id = p.engagement_id WHERE p.id = :id"
            ),
            {"id": policy_id},
        ).mappings().one_or_none()
        if policy is None:
            raise LookupError("policy not found")
        rows = list(connection.execute(
            text(
                "SELECT text, control_ids, parameters_used, faithful FROM statements "
                "WHERE policy_id = :id ORDER BY seq"
            ),
            {"id": policy_id},
        ).mappings())
    if not rows or any(not row["faithful"] for row in rows):
        raise ValueError("policy is not fully faithfulness-verified")
    statements = [
        GeneratedStatement.model_validate({key: value for key, value in row.items() if key != "faithful"})
        for row in rows
    ]
    company_name = str(policy["company"].get("company_name") or policy["company"].get("name") or "Company")
    filename = f"{policy['policy_type'].lower().replace(' ', '-')}-v{policy['version']}.docx"
    return filename, export_policy_docx(
        title=f"{policy['policy_type']} Policy",
        company_name=company_name,
        policy_type=policy["policy_type"],
        generated_at=policy["created_at"],
        ruleset_version="verified-controls",
        statements=statements,
    )


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
