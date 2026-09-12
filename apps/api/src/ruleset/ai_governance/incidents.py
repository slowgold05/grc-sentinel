from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import Engine, text

from ruleset.ai_governance.models import IncidentSeverity


class IncidentState(StrEnum):
    CREATED = "created"
    TRIAGED = "triaged"
    CONTAINED = "contained"
    RESOLVED = "resolved"


_NEXT = {
    IncidentState.CREATED: IncidentState.TRIAGED,
    IncidentState.TRIAGED: IncidentState.CONTAINED,
    IncidentState.CONTAINED: IncidentState.RESOLVED,
}


class IncidentFacts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: IncidentSeverity
    impact: str = Field(min_length=1, max_length=10_000)
    action: str = Field(min_length=1, max_length=10_000)
    owner: str = Field(min_length=1, max_length=500)
    regulatory_review_required: bool
    risk_ids: list[UUID] = Field(default_factory=list, max_length=50)
    evaluation_run_ids: list[UUID] = Field(default_factory=list, max_length=50)
    evidence_ids: list[UUID] = Field(default_factory=list, max_length=50)

    @field_validator("risk_ids", "evaluation_run_ids", "evidence_ids")
    @classmethod
    def unique_links(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("linked record IDs must be unique")
        return value


class IncidentCreate(IncidentFacts):
    title: str = Field(min_length=1, max_length=500)


class IncidentTransition(IncidentFacts):
    state: IncidentState
    expected_latest_event_id: UUID


class IncidentRecord(IncidentFacts):
    id: UUID
    ai_system_id: UUID
    title: str
    state: IncidentState
    latest_event_id: UUID
    recorded_by: str
    recorded_at: datetime


class IncidentStaleError(Exception):
    pass


def _validate_links(connection, system_id: UUID, facts: IncidentFacts) -> None:
    counts = (
        (
            facts.risk_ids,
            connection.execute(
                text("SELECT count(*) FROM risks WHERE id = ANY(:ids)"),
                {"ids": facts.risk_ids},
            ).scalar_one()
            if facts.risk_ids
            else 0,
        ),
        (
            facts.evaluation_run_ids,
            connection.execute(
                text(
                    "SELECT count(*) FROM ai_evaluation_runs r JOIN ai_evaluation_definitions d "
                    "ON d.id = r.definition_id WHERE r.id = ANY(:ids) AND d.ai_system_id = :system"
                ),
                {"ids": facts.evaluation_run_ids, "system": system_id},
            ).scalar_one()
            if facts.evaluation_run_ids
            else 0,
        ),
        (
            facts.evidence_ids,
            connection.execute(
                text("SELECT count(*) FROM control_evidence WHERE id = ANY(:ids)"),
                {"ids": facts.evidence_ids},
            ).scalar_one()
            if facts.evidence_ids
            else 0,
        ),
    )
    if any(count != len(ids) for ids, count in counts):
        raise ValueError("linked record is missing, cross-tenant, or belongs to another system")


def _insert_event(
    connection,
    org_id: UUID,
    incident_id: UUID,
    state: IncidentState,
    actor: str,
    facts: IncidentFacts,
):
    return (
        connection.execute(
            text(
                "INSERT INTO ai_incident_events (org_id, incident_id, state, severity, impact, action, "
                "owner, regulatory_review_required, risk_ids, evaluation_run_ids, evidence_ids, recorded_by) "
                "VALUES (:org, :incident, :state, :severity, :impact, :action, :owner, :review, :risks, "
                ":evaluations, :evidence, :actor) RETURNING id, recorded_at"
            ),
            {
                "org": org_id,
                "incident": incident_id,
                "state": state.value,
                "severity": facts.severity.value,
                "impact": facts.impact,
                "action": facts.action,
                "owner": facts.owner,
                "review": facts.regulatory_review_required,
                "risks": facts.risk_ids,
                "evaluations": facts.evaluation_run_ids,
                "evidence": facts.evidence_ids,
                "actor": actor,
            },
        )
        .mappings()
        .one()
    )


def create_incident(
    engine: Engine, org_id: UUID, system_id: UUID, actor: str, request: IncidentCreate
) -> UUID:
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        engagement_id = connection.execute(
            text("SELECT engagement_id FROM ai_systems WHERE id = :id"), {"id": system_id}
        ).scalar_one_or_none()
        if engagement_id is None:
            raise LookupError("AI system not found")
        _validate_links(connection, system_id, request)
        incident_id = connection.execute(
            text(
                "INSERT INTO ai_incidents (org_id, engagement_id, ai_system_id, title, created_by) "
                "VALUES (:org, :engagement, :system, :title, :actor) RETURNING id"
            ),
            {
                "org": org_id,
                "engagement": engagement_id,
                "system": system_id,
                "title": request.title,
                "actor": actor,
            },
        ).scalar_one()
        _insert_event(connection, org_id, incident_id, IncidentState.CREATED, actor, request)
    return incident_id


def transition_incident(
    engine: Engine, org_id: UUID, incident_id: UUID, actor: str, request: IncidentTransition
) -> None:
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        incident = (
            connection.execute(
                text("SELECT ai_system_id FROM ai_incidents WHERE id = :id"), {"id": incident_id}
            )
            .mappings()
            .one_or_none()
        )
        if incident is None:
            raise LookupError("incident not found")
        latest = (
            connection.execute(
                text(
                    "SELECT id, state FROM ai_incident_events WHERE incident_id = :id ORDER BY recorded_at DESC, id DESC LIMIT 1"
                ),
                {"id": incident_id},
            )
            .mappings()
            .one()
        )
        if latest["id"] != request.expected_latest_event_id:
            raise IncidentStaleError("incident changed; refresh before updating")
        if _NEXT.get(IncidentState(latest["state"])) != request.state:
            raise ValueError("invalid incident state transition")
        _validate_links(connection, incident["ai_system_id"], request)
        _insert_event(connection, org_id, incident_id, request.state, actor, request)


def list_incidents(engine: Engine, org_id: UUID, system_id: UUID) -> list[IncidentRecord]:
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        rows = connection.execute(
            text(
                "SELECT i.id, i.ai_system_id, i.title, e.id AS latest_event_id, e.state, e.severity, "
                "e.impact, e.action, e.owner, e.regulatory_review_required, e.risk_ids, "
                "e.evaluation_run_ids, e.evidence_ids, e.recorded_by, e.recorded_at FROM ai_incidents i "
                "JOIN LATERAL (SELECT * FROM ai_incident_events WHERE incident_id = i.id "
                "ORDER BY recorded_at DESC, id DESC LIMIT 1) e ON true WHERE i.ai_system_id = :system "
                "ORDER BY e.recorded_at DESC"
            ),
            {"system": system_id},
        ).mappings()
        return [IncidentRecord.model_validate(row) for row in rows]
