from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import text

from ruleset.database import engine
from ruleset.gap_analysis import list_required_controls


def test_required_controls_combine_regulations_and_assurance_objectives() -> None:
    org_id, engagement_id = uuid4(), uuid4()
    regulation_id, regulation_control = uuid4(), uuid4()
    regulation_framework_id, framework_id, assurance_control = uuid4(), uuid4(), uuid4()
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        connection.execute(
            text("INSERT INTO orgs (id, name) VALUES (:id, 'required controls')"), {"id": org_id}
        )
        connection.execute(
            text(
                "INSERT INTO engagements (id, org_id, company, expires_at) VALUES (:id, :org_id, '{}', :expires)"
            ),
            {
                "id": engagement_id,
                "org_id": org_id,
                "expires": datetime.now(UTC) + timedelta(days=1),
            },
        )
        connection.execute(
            text(
                "INSERT INTO regulations (id, name, jurisdiction, citation) VALUES (:id, :name, 'test', 'test')"
            ),
            {"id": regulation_id, "name": f"required-{regulation_id}"},
        )
        connection.execute(
            text(
                "INSERT INTO frameworks (id, name, version, publisher, machine_readable_source) VALUES (:id, :name, '1', 'test', 'test')"
            ),
            [
                {"id": regulation_framework_id, "name": f"required-{regulation_framework_id}"},
                {"id": framework_id, "name": f"required-{framework_id}"},
            ],
        )
        connection.execute(
            text(
                "INSERT INTO controls (id, framework_id, control_code, title, description) VALUES (:id, :framework, :code, 'Test', 'Test')"
            ),
            [
                {
                    "id": regulation_control,
                    "framework": regulation_framework_id,
                    "code": f"R-{regulation_control}",
                },
                {
                    "id": assurance_control,
                    "framework": framework_id,
                    "code": f"A-{assurance_control}",
                },
            ],
        )
        connection.execute(
            text("INSERT INTO regulation_controls VALUES (:regulation, :control, 'test')"),
            {"regulation": regulation_id, "control": regulation_control},
        )
        connection.execute(
            text(
                "INSERT INTO determinations (org_id, engagement_id, regulation_id, rule_id, rule_version, facts) VALUES (:org, :engagement, :regulation, 'test', 1, '{}')"
            ),
            {"org": org_id, "engagement": engagement_id, "regulation": regulation_id},
        )
        connection.execute(
            text(
                "INSERT INTO assurance_objectives (org_id, engagement_id, framework_id, basis, selected_by) VALUES (:org, :engagement, :framework, 'company_strategy', 'test')"
            ),
            {"org": org_id, "engagement": engagement_id, "framework": framework_id},
        )
    try:
        assert {row.id for row in list_required_controls(engine, org_id, engagement_id)} == {
            regulation_control,
            assurance_control,
        }
    finally:
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
            )
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
            connection.execute(
                text("DELETE FROM regulations WHERE id = :id"), {"id": regulation_id}
            )
            connection.execute(
                text("DELETE FROM frameworks WHERE id IN (:regulation, :assurance)"),
                {"regulation": regulation_framework_id, "assurance": framework_id},
            )
