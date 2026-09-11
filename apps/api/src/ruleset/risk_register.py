from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Engine, text


class Risk(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: UUID
    title: str
    description: str
    likelihood: int = Field(ge=1, le=5)
    impact: int = Field(ge=1, le=5)
    score: int = Field(ge=1, le=25)
    status: Literal["open", "mitigating", "accepted", "closed"]
    treatment: str
    control_ids: list[str]
    ai_system_id: UUID | None = None


class RiskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10_000)
    likelihood: int = Field(ge=1, le=5)
    impact: int = Field(ge=1, le=5)
    treatment: str = Field(default="", max_length=10_000)
    control_ids: list[str] = Field(default_factory=list, max_length=100)
    ai_system_id: UUID | None = None


class RiskStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["open", "mitigating", "accepted", "closed"]


def _set_org(connection: object, org_id: UUID) -> None:
    connection.execute(
        text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
    )


def create_risk(
    engine: Engine,
    org_id: UUID,
    *,
    title: str,
    description: str,
    likelihood: int,
    impact: int,
    treatment: str = "",
    control_ids: list[str] | None = None,
    ai_system_id: UUID | None = None,
) -> UUID:
    if not title.strip() or not description.strip() or not 1 <= likelihood <= 5 or not 1 <= impact <= 5:
        raise ValueError("risk title, description, likelihood, and impact are invalid")
    with engine.begin() as connection:
        _set_org(connection, org_id)
        if ai_system_id is not None and connection.execute(
            text("SELECT id FROM ai_systems WHERE id = :id"), {"id": ai_system_id}
        ).scalar_one_or_none() is None:
            raise LookupError("AI system not found")
        return connection.execute(
            text(
                "INSERT INTO risks "
                "(org_id, title, description, likelihood, impact, treatment, control_ids, ai_system_id) VALUES "
                "(:org_id, :title, :description, :likelihood, :impact, :treatment, :control_ids, :ai_system_id) "
                "RETURNING id"
            ),
            {
                "org_id": org_id,
                "title": title,
                "description": description,
                "likelihood": likelihood,
                "impact": impact,
                "treatment": treatment,
                "control_ids": control_ids or [],
                "ai_system_id": ai_system_id,
            },
        ).scalar_one()


def list_risks(engine: Engine, org_id: UUID) -> list[Risk]:
    with engine.begin() as connection:
        _set_org(connection, org_id)
        rows = connection.execute(
            text("SELECT * FROM risks ORDER BY score DESC, created_at DESC")
        ).mappings()
        return [Risk.model_validate(row) for row in rows]


def update_risk_status(
    engine: Engine,
    org_id: UUID,
    risk_id: UUID,
    status: Literal["open", "mitigating", "accepted", "closed"],
) -> bool:
    with engine.begin() as connection:
        _set_org(connection, org_id)
        return bool(
            connection.execute(
                text("UPDATE risks SET status = :status WHERE id = :id"),
                {"status": status, "id": risk_id},
            ).rowcount
        )


def delete_risk(engine: Engine, org_id: UUID, risk_id: UUID) -> bool:
    with engine.begin() as connection:
        _set_org(connection, org_id)
        return bool(
            connection.execute(text("DELETE FROM risks WHERE id = :id"), {"id": risk_id}).rowcount
        )
