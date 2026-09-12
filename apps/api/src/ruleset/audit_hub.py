from datetime import UTC, datetime
import hashlib
import secrets
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import Engine, text


class AuditShare(BaseModel):
    org_id: UUID
    engagement_id: UUID
    company: dict[str, object]
    policies: list[dict[str, object]]
    coverage: list[dict[str, object]]
    ai_system: dict[str, object] | None = None
    assessments: list[dict[str, object]] = Field(default_factory=list)
    objectives: list[dict[str, object]] = Field(default_factory=list)
    risks: list[dict[str, object]] = Field(default_factory=list)
    evaluations: list[dict[str, object]] = Field(default_factory=list)
    approvals: list[dict[str, object]] = Field(default_factory=list)
    evidence: list[dict[str, object]] = Field(default_factory=list)
    incidents: list[dict[str, object]] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)


class AuditShareCreate(BaseModel):
    expires_in_hours: int = Field(default=24, ge=1, le=168)


class AuditShareCreated(BaseModel):
    token: str
    expires_at: datetime


class AIDashboard(BaseModel):
    inventory: int
    risk_distribution: dict[str, int]
    overdue_reviews: int
    governance_blockers: int
    failed_evaluations: int
    open_incidents: int
    expiring_exceptions: int


def _digest(token: str) -> bytes:
    return hashlib.sha256(token.encode()).digest()


def create_share_link(
    engine: Engine,
    org_id: UUID,
    engagement_id: UUID,
    expires_at: datetime,
    *,
    ai_system_id: UUID | None = None,
) -> str:
    """Create a bearer token while storing only its hash."""
    if expires_at <= datetime.now(UTC):
        raise ValueError("share expiry must be in the future")
    token = secrets.token_urlsafe(32)
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        if (
            connection.execute(
                text("SELECT 1 FROM engagements WHERE id = :id"), {"id": engagement_id}
            ).scalar_one_or_none()
            is None
        ):
            raise LookupError("engagement not found")
        if (
            ai_system_id is not None
            and connection.execute(
                text("SELECT 1 FROM ai_systems WHERE id = :id AND engagement_id = :engagement"),
                {"id": ai_system_id, "engagement": engagement_id},
            ).scalar_one_or_none()
            is None
        ):
            raise LookupError("AI system not found in engagement")
        connection.execute(
            text(
                "INSERT INTO audit_share_links "
                "(org_id, engagement_id, ai_system_id, token_hash, expires_at) "
                "VALUES (:org_id, :engagement_id, :ai_system_id, :token_hash, :expires_at)"
            ),
            {
                "org_id": org_id,
                "engagement_id": engagement_id,
                "token_hash": _digest(token),
                "expires_at": expires_at,
                "ai_system_id": ai_system_id,
            },
        )
    return token


def resolve_share(engine: Engine, token: str) -> AuditShare | None:
    """Resolve a valid share, set its constrained tenant context, and log access."""
    if len(token) < 32:
        return None
    with engine.begin() as connection:
        share = (
            connection.execute(
                text("SELECT * FROM resolve_audit_share(:token_hash)"),
                {"token_hash": _digest(token)},
            )
            .mappings()
            .one_or_none()
        )
        if share is None:
            return None
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"),
            {"org_id": str(share["org_id"])},
        )
        company = connection.execute(
            text("SELECT company FROM engagements WHERE id = :id"),
            {"id": share["engagement_id"]},
        ).scalar_one()
        system_id = share["ai_system_id"]
        policy_scope = "AND ai_system_id = :system" if system_id is not None else ""
        policies = list(
            connection.execute(
                text(
                    "SELECT id, policy_type, version, created_at FROM policies "
                    f"WHERE engagement_id = :id {policy_scope} ORDER BY created_at"
                ),
                {"id": share["engagement_id"], "system": system_id},
            ).mappings()
        )
        coverage = list(
            connection.execute(
                text(
                    "SELECT control_id, status, evidence_quote, gap FROM coverage_results "
                    "WHERE engagement_id = :id ORDER BY control_id"
                ),
                {"id": share["engagement_id"]},
            ).mappings()
        )
        ai_system = None
        assessments = objectives = risks = evaluations = approvals = evidence = incidents = []
        exclusions: list[str] = []
        if system_id is not None:
            coverage = []
            ai_system = dict(
                connection.execute(
                    text(
                        "SELECT id, name, description, owner_name, business_purpose, profile, status, "
                        "deployment_date, next_review_date FROM ai_systems WHERE id = :id"
                    ),
                    {"id": system_id},
                )
                .mappings()
                .one()
            )
            queries = {
                "assessments": "SELECT id, version, status, missing_facts, reviewer, source_versions, created_at FROM ai_impact_assessment_versions WHERE ai_system_id = :id ORDER BY version",
                "objectives": "SELECT id, framework, source_version, objective_type, basis, scope, target_date FROM ai_assurance_objectives WHERE ai_system_id = :id ORDER BY created_at",
                "risks": "SELECT id, title, likelihood, impact, score, status, treatment, control_ids FROM risks WHERE ai_system_id = :id ORDER BY created_at",
                "evaluations": "SELECT d.id AS definition_id, d.name, d.evaluation_type, d.version, d.dataset_version, r.result, r.measured_value, r.tested_at FROM ai_evaluation_definitions d LEFT JOIN ai_evaluation_runs r ON r.definition_id = d.id WHERE d.ai_system_id = :id ORDER BY d.name, d.version, r.tested_at",
                "approvals": "SELECT id, decision_type, outcome, rationale, expires_at, decided_by, decided_at FROM ai_governance_decisions WHERE ai_system_id = :id ORDER BY decided_at",
                "incidents": "SELECT i.id, i.title, e.state, e.severity, e.impact, e.owner, e.regulatory_review_required, e.recorded_at FROM ai_incidents i JOIN LATERAL (SELECT * FROM ai_incident_events WHERE incident_id = i.id ORDER BY recorded_at DESC, id DESC LIMIT 1) e ON true WHERE i.ai_system_id = :id ORDER BY e.recorded_at",
                "evidence": "SELECT id, test_id, status, control_ids, tested_at FROM control_evidence WHERE id IN (SELECT unnest(evidence_ids) FROM ai_incident_events e JOIN ai_incidents i ON i.id = e.incident_id WHERE i.ai_system_id = :id) ORDER BY tested_at",
            }
            values = {
                name: [
                    dict(row)
                    for row in connection.execute(text(query), {"id": system_id}).mappings()
                ]
                for name, query in queries.items()
            }
            assessments, objectives, risks = (
                values["assessments"],
                values["objectives"],
                values["risks"],
            )
            evaluations, approvals = values["evaluations"], values["approvals"]
            evidence, incidents = values["evidence"], values["incidents"]
            exclusions = [
                "Candidate legal triage is not a legal determination.",
                "Only evidence explicitly linked to this AI system's incidents is included.",
                "Framework objectives represent selected goals, not certification.",
            ]
        connection.execute(
            text(
                "INSERT INTO audit_events (org_id, engagement_id, event_type, details) "
                "VALUES (:org_id, :engagement_id, 'share_accessed', "
                "jsonb_build_object('share_id', CAST(:share_id AS text)))"
            ),
            {
                "org_id": share["org_id"],
                "engagement_id": share["engagement_id"],
                "share_id": share["share_id"],
            },
        )
    return AuditShare(
        org_id=share["org_id"],
        engagement_id=share["engagement_id"],
        company=company,
        policies=[dict(row) for row in policies],
        coverage=[dict(row) for row in coverage],
        ai_system=ai_system,
        assessments=assessments,
        objectives=objectives,
        risks=risks,
        evaluations=evaluations,
        approvals=approvals,
        evidence=evidence,
        incidents=incidents,
        exclusions=exclusions,
    )


def get_ai_dashboard(engine: Engine, org_id: UUID) -> AIDashboard:
    """Summarize explicit current AI-governance records for one tenant."""
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})

        def scalar(query: str) -> int:
            return connection.execute(text(query)).scalar_one()

        risk_rows = connection.execute(
            text(
                "SELECT status, count(*) AS count FROM risks WHERE ai_system_id IS NOT NULL GROUP BY status"
            )
        ).mappings()
        risk_distribution = {row["status"]: row["count"] for row in risk_rows}
        inventory = scalar("SELECT count(*) FROM ai_systems")
        failed = scalar(
            "SELECT count(*) FROM ai_evaluation_runs r WHERE r.result = 'fail' AND NOT EXISTS "
            "(SELECT 1 FROM ai_evaluation_runs newer WHERE newer.definition_id = r.definition_id "
            "AND (newer.tested_at, newer.id) > (r.tested_at, r.id))"
        )
        overdue = scalar("SELECT count(*) FROM ai_systems WHERE next_review_date < current_date")
        open_incidents = scalar(
            "SELECT count(*) FROM ai_incidents i JOIN LATERAL (SELECT state FROM ai_incident_events "
            "WHERE incident_id = i.id ORDER BY recorded_at DESC, id DESC LIMIT 1) e ON true "
            "WHERE e.state <> 'resolved'"
        )
        expiring = scalar(
            "SELECT count(*) FROM ai_governance_decisions d WHERE decision_type = 'exception' "
            "AND outcome IN ('approved', 'conditional') AND expires_at > now() "
            "AND expires_at <= now() + interval '30 days' AND NOT EXISTS (SELECT 1 FROM "
            "ai_governance_decisions newer WHERE newer.ai_system_id = d.ai_system_id "
            "AND newer.decision_type = 'exception' AND (newer.decided_at, newer.id) > (d.decided_at, d.id))"
        )
    return AIDashboard(
        inventory=inventory,
        risk_distribution=risk_distribution,
        overdue_reviews=overdue,
        governance_blockers=overdue + failed + open_incidents,
        failed_evaluations=failed,
        open_incidents=open_incidents,
        expiring_exceptions=expiring,
    )


def revoke_share(engine: Engine, org_id: UUID, token: str) -> bool:
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        return bool(
            connection.execute(
                text(
                    "UPDATE audit_share_links SET revoked_at = now() "
                    "WHERE token_hash = :token_hash AND revoked_at IS NULL"
                ),
                {"token_hash": _digest(token)},
            ).rowcount
        )
