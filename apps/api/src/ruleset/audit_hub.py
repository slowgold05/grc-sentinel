from datetime import UTC, datetime
import hashlib
import secrets
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Engine, text


class AuditShare(BaseModel):
    org_id: UUID
    engagement_id: UUID
    company: dict[str, object]
    policies: list[dict[str, object]]
    coverage: list[dict[str, object]]


def _digest(token: str) -> bytes:
    return hashlib.sha256(token.encode()).digest()


def create_share_link(
    engine: Engine, org_id: UUID, engagement_id: UUID, expires_at: datetime
) -> str:
    """Create a bearer token while storing only its hash."""
    if expires_at <= datetime.now(UTC):
        raise ValueError("share expiry must be in the future")
    token = secrets.token_urlsafe(32)
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        connection.execute(
            text(
                "INSERT INTO audit_share_links (org_id, engagement_id, token_hash, expires_at) "
                "VALUES (:org_id, :engagement_id, :token_hash, :expires_at)"
            ),
            {
                "org_id": org_id,
                "engagement_id": engagement_id,
                "token_hash": _digest(token),
                "expires_at": expires_at,
            },
        )
    return token


def resolve_share(engine: Engine, token: str) -> AuditShare | None:
    """Resolve a valid share, set its constrained tenant context, and log access."""
    if len(token) < 32:
        return None
    with engine.begin() as connection:
        share = connection.execute(
            text("SELECT * FROM resolve_audit_share(:token_hash)"),
            {"token_hash": _digest(token)},
        ).mappings().one_or_none()
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
        policies = list(
            connection.execute(
                text(
                    "SELECT id, policy_type, version, created_at FROM policies "
                    "WHERE engagement_id = :id ORDER BY created_at"
                ),
                {"id": share["engagement_id"]},
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
