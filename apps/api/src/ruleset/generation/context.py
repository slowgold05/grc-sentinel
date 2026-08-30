from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Engine, bindparam, text

from ruleset.generation.models import RetrievedControl


class PolicySectionPlan(BaseModel):
    """Deterministic template section and its required database controls."""

    section: str
    template_body: str
    control_ids: list[UUID]


def plan_policy(engine: Engine, policy_type: str) -> list[PolicySectionPlan]:
    """Load a policy's ordered section plan without model involvement."""
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT section, template_body, control_ids FROM policy_templates "
                "WHERE policy_type = :policy_type ORDER BY section"
            ),
            {"policy_type": policy_type},
        ).mappings()
        return [PolicySectionPlan.model_validate(row) for row in rows]


def retrieve_controls(engine: Engine, control_ids: list[UUID]) -> list[RetrievedControl]:
    """Retrieve exact current control text and parameters for the planned IDs."""
    if not control_ids:
        return []
    statement = text(
        "SELECT control_code AS control_id, title || E'\\n' || description AS text, params AS parameters "
        "FROM controls WHERE id IN :ids AND valid_to IS NULL ORDER BY control_code"
    ).bindparams(bindparam("ids", expanding=True))
    with engine.connect() as connection:
        return [
            RetrievedControl.model_validate(row)
            for row in connection.execute(statement, {"ids": control_ids}).mappings()
        ]
