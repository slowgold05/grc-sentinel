import json
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, JsonValue
from sqlalchemy import Engine, text

from ruleset.monitoring.models import ControlTest, TestResult


class EvidenceRecord(BaseModel):
    id: UUID
    test_id: str
    status: str
    observed: dict[str, JsonValue]
    control_ids: list[str]
    tested_at: datetime


def list_evidence(engine: Engine, org_id: UUID) -> list[EvidenceRecord]:
    """Return the tenant's newest 100 immutable evidence records."""
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        rows = connection.execute(
            text(
                "SELECT id, test_id, status, observed, control_ids, tested_at "
                "FROM control_evidence ORDER BY tested_at DESC LIMIT 100"
            )
        ).mappings()
    return [EvidenceRecord.model_validate(row) for row in rows]


def is_control_drift(previous_status: str | None, current_status: str) -> bool:
    """Only a pass-to-fail transition is actionable control drift."""
    return previous_status == "pass" and current_status == "fail"


def append_evidence(
    engine: Engine,
    org_id: UUID,
    test: ControlTest,
    result: TestResult,
    raw_response: dict[str, JsonValue],
) -> UUID:
    """Append one immutable evidence record within the tenant context."""
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        evidence_id = connection.execute(
            text(
                "INSERT INTO control_evidence "
                "(org_id, test_id, status, observed, raw_response, control_ids, tested_at) "
                "VALUES (:org_id, :test_id, :status, CAST(:observed AS jsonb), "
                "CAST(:raw_response AS jsonb), :control_ids, :tested_at) RETURNING id"
            ),
            {
                "org_id": org_id,
                "test_id": test.test_id,
                "status": result.status,
                "observed": json.dumps(result.observed),
                "raw_response": json.dumps(raw_response),
                "control_ids": test.control_ids,
                "tested_at": result.tested_at,
            },
        ).scalar_one()
    return evidence_id
