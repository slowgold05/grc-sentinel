from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Engine, text


class SweepResult(BaseModel):
    """Counts removed by one retention sweep."""

    expired_uploads: int
    expired_engagements: int
    expired_osint: int
    expired_evidence: int
    expired_audit_events: int
    expired_share_links: int


def sweep_expired(engine: Engine, now: datetime) -> SweepResult:
    """Delete expired uploads, engagements, and OSINT through the constrained DB function."""
    with engine.begin() as connection:
        row = connection.execute(
            text("SELECT * FROM sweep_expired(:now)"), {"now": now}
        ).mappings().one()
    return SweepResult.model_validate(row)
