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
) -> UUID:
    if not title.strip() or not description.strip() or not 1 <= likelihood <= 5 or not 1 <= impact <= 5:
        raise ValueError("risk title, description, likelihood, and impact are invalid")
    with engine.begin() as connection:
        _set_org(connection, org_id)
        return connection.execute(
            text(
                "INSERT INTO risks "
                "(org_id, title, description, likelihood, impact, treatment, control_ids) VALUES "
                "(:org_id, :title, :description, :likelihood, :impact, :treatment, :control_ids) "
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
