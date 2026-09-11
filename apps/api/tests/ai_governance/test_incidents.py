from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import text

from ruleset.ai_governance.incidents import (
    IncidentCreate,
    IncidentStaleError,
    IncidentTransition,
    create_incident,
    list_incidents,
    transition_incident,
)
from ruleset.database import engine


def _facts(**overrides):
    return {
        "severity": "high",
        "impact": "Incorrect answers reached an internal reviewer.",
        "action": "Disable the affected prompt version.",
        "owner": "AI operations",
        "regulatory_review_required": True,
        **overrides,
    }


def test_incident_history_is_ordered_tenant_safe_and_append_only() -> None:
    org_a, org_b = uuid4(), uuid4()
    engagement_a, engagement_b, system_id, foreign_risk = uuid4(), uuid4(), uuid4(), uuid4()
    with engine.begin() as connection:
        for org_id in (org_a, org_b):
            connection.execute(
                text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)}
            )
            connection.execute(
                text("INSERT INTO orgs (id, name) VALUES (:id, 'incident test')"), {"id": org_id}
            )
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_a)})
        connection.execute(
            text(
                "INSERT INTO engagements (id, org_id, company, expires_at) "
                "VALUES (:id, :org, '{}', :expires)"
            ),
            {"id": engagement_a, "org": org_a, "expires": datetime.now(UTC) + timedelta(days=1)},
        )
        connection.execute(
            text(
                "INSERT INTO ai_systems (id, org_id, engagement_id, name, description, "
                "owner_name, business_purpose, profile) VALUES (:id, :org, :engagement, "
                "'Assistant', 'Test', 'Owner', 'Test', '{}')"
            ),
            {"id": system_id, "org": org_a, "engagement": engagement_a},
        )
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_b)})
        connection.execute(
            text(
                "INSERT INTO engagements (id, org_id, company, expires_at) "
                "VALUES (:id, :org, '{}', :expires)"
            ),
            {"id": engagement_b, "org": org_b, "expires": datetime.now(UTC) + timedelta(days=1)},
        )
        connection.execute(
            text(
                "INSERT INTO risks (id, org_id, title, description, likelihood, impact, control_ids) "
                "VALUES (:id, :org, 'Foreign', 'Foreign', 1, 1, '{}')"
            ),
            {"id": foreign_risk, "org": org_b},
        )
    try:
        with pytest.raises(ValueError, match="cross-tenant"):
            create_incident(
                engine,
                org_a,
                system_id,
                "reviewer-a",
                IncidentCreate(title="Grounding issue", **_facts(risk_ids=[foreign_risk])),
            )
        incident_id = create_incident(
            engine,
            org_a,
            system_id,
            "reviewer-a",
            IncidentCreate(title="Grounding issue", **_facts()),
        )
        created = list_incidents(engine, org_a, system_id)[0]
        assert created.state == "created"
        assert list_incidents(engine, org_b, system_id) == []

        with pytest.raises(ValueError, match="invalid incident state"):
            transition_incident(
                engine,
                org_a,
                incident_id,
                "reviewer-a",
                IncidentTransition(
                    state="resolved", expected_latest_event_id=created.latest_event_id, **_facts()
                ),
            )
        transition_incident(
            engine,
            org_a,
            incident_id,
            "reviewer-a",
            IncidentTransition(
                state="triaged", expected_latest_event_id=created.latest_event_id, **_facts()
            ),
        )
        with pytest.raises(IncidentStaleError):
            transition_incident(
                engine,
                org_a,
                incident_id,
                "reviewer-a",
                IncidentTransition(
                    state="contained", expected_latest_event_id=created.latest_event_id, **_facts()
                ),
            )
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_a)}
            )
            assert (
                connection.execute(
                    text("SELECT count(*) FROM ai_incident_events WHERE incident_id = :id"),
                    {"id": incident_id},
                ).scalar_one()
                == 2
            )
            assert (
                connection.execute(
                    text(
                        "UPDATE ai_incident_events SET action = 'tampered' WHERE incident_id = :id"
                    ),
                    {"id": incident_id},
                ).rowcount
                == 0
            )
    finally:
        with engine.begin() as connection:
            for org_id in (org_a, org_b):
                connection.execute(
                    text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)}
                )
                connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
