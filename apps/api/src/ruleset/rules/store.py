import json
from uuid import UUID

from sqlalchemy import Engine, text

from ruleset.errors import UnknownRegulationError
from ruleset.rules.models import Determination


def store_determinations(
    engine: Engine,
    org_id: UUID,
    engagement_id: UUID,
    determinations: list[Determination],
) -> int:
    """Append new determinations in one tenant-scoped transaction."""
    stored = 0
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"),
            {"org_id": str(org_id)},
        )
        for determination in determinations:
            regulation_id = connection.execute(
                text("SELECT id FROM regulations WHERE name = :name"),
                {"name": determination.regulation},
            ).scalar_one_or_none()
            if regulation_id is None:
                raise UnknownRegulationError(determination.regulation)
            inserted = connection.execute(
                text(
                    "INSERT INTO determinations "
                    "(org_id, engagement_id, regulation_id, rule_id, rule_version, facts) "
                    "VALUES (:org_id, :engagement_id, :regulation_id, :rule_id, "
                    ":rule_version, CAST(:facts AS jsonb)) "
                    "ON CONFLICT (engagement_id, rule_id, rule_version) DO NOTHING RETURNING id"
                ),
                {
                    "org_id": org_id,
                    "engagement_id": engagement_id,
                    "regulation_id": regulation_id,
                    "rule_id": determination.rule_id,
                    "rule_version": determination.rule_version,
                    "facts": json.dumps(determination.facts),
                },
            ).scalar_one_or_none()
            stored += inserted is not None
    return stored

