from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Engine, text

from ruleset.intake.models import CompanyIntake
from ruleset.rules.engine import evaluate
from ruleset.rules.loader import load_rules
from ruleset.rules.models import CompanyFacts, Determination
from ruleset.rules.store import insert_determinations

_HIPAA_RULES = Path(__file__).parent / "rules" / "rulesets" / "hipaa-v2.json"


class EngagementCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company: CompanyIntake
    retention_days: int = Field(default=90, ge=1, le=365)


class EngagementCreated(BaseModel):
    id: UUID
    determinations: list[Determination]


class EngagementSummary(BaseModel):
    id: UUID
    company: CompanyIntake
    created_at: datetime
    expires_at: datetime
    regulations: list[str]


def create_engagement(
    engine: Engine, org_id: UUID, request: EngagementCreate
) -> EngagementCreated:
    """Create an engagement and persist deterministic applicability evidence."""
    facts = CompanyFacts(
        {
            "employee_count": request.company.employee_count,
            "geos": request.company.geos,
            "data_types": request.company.data_types,
            "sends_external_email": request.company.sends_external_email,
            "cloud_providers": request.company.cloud_providers,
        }
    )
    determinations = evaluate(facts, load_rules(_HIPAA_RULES))
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        engagement_id = connection.execute(
            text(
                "INSERT INTO engagements (org_id, company, expires_at) "
                "VALUES (:org_id, CAST(:company AS jsonb), :expires_at) RETURNING id"
            ),
            {
                "org_id": org_id,
                "company": json.dumps(request.company.model_dump(mode="json")),
                "expires_at": datetime.now(UTC) + timedelta(days=request.retention_days),
            },
        ).scalar_one()
        insert_determinations(connection, org_id, engagement_id, determinations)
    return EngagementCreated(id=engagement_id, determinations=determinations)


def list_engagements(engine: Engine, org_id: UUID) -> list[EngagementSummary]:
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        rows = connection.execute(
            text(
                "SELECT e.id, e.company, e.created_at, e.expires_at, "
                "COALESCE(array_agg(r.name) FILTER (WHERE r.name IS NOT NULL), '{}') AS regulations "
                "FROM engagements e LEFT JOIN determinations d ON d.engagement_id = e.id "
                "LEFT JOIN regulations r ON r.id = d.regulation_id "
                "GROUP BY e.id ORDER BY e.created_at DESC"
            )
        ).mappings()
        return [EngagementSummary.model_validate(row) for row in rows]
