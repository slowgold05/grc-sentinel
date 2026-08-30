import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import Engine, text


def cache_result(
    engine: Engine, org_id: UUID, domain: str, module: str, result: dict[str, Any]
) -> None:
    """Upsert one tenant's OSINT result with a fresh 30-day expiry."""
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        connection.execute(
            text(
                "INSERT INTO osint_cache (org_id, domain, module, result, expires_at) "
                "VALUES (:org, :domain, :module, CAST(:result AS jsonb), :expires) "
                "ON CONFLICT (org_id, domain, module) DO UPDATE SET result = EXCLUDED.result, "
                "expires_at = EXCLUDED.expires_at"
            ),
            {
                "org": org_id,
                "domain": domain.lower(),
                "module": module,
                "result": json.dumps(result),
                "expires": datetime.now(UTC) + timedelta(days=30),
            },
        )


def load_cached_result(
    engine: Engine, org_id: UUID, domain: str, module: str
) -> dict[str, Any] | None:
    """Return an unexpired result visible to the tenant."""
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        return connection.execute(
            text(
                "SELECT result FROM osint_cache WHERE domain = :domain AND module = :module "
                "AND expires_at > now()"
            ),
            {"domain": domain.lower(), "module": module},
        ).scalar_one_or_none()
