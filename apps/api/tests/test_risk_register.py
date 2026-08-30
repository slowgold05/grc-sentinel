from uuid import uuid4

from sqlalchemy import create_engine, text

from ruleset.config import settings
from ruleset.risk_register import create_risk, delete_risk, list_risks, update_risk_status


def test_risk_lifecycle_uses_database_score() -> None:
    engine = create_engine(str(settings.database_url))
    org_id = uuid4()
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        connection.execute(
            text("INSERT INTO orgs (id, name) VALUES (:id, 'risk test')"), {"id": org_id}
        )
    try:
        risk_id = create_risk(
            engine,
            org_id,
            title="Credential compromise",
            description="An administrator credential may be compromised.",
            likelihood=3,
            impact=5,
            control_ids=["IA-2"],
        )
        assert list_risks(engine, org_id)[0].score == 15
        assert update_risk_status(engine, org_id, risk_id, "mitigating")
        assert list_risks(engine, org_id)[0].status == "mitigating"
        assert delete_risk(engine, org_id, risk_id)
        assert list_risks(engine, org_id) == []
    finally:
        with engine.begin() as connection:
            connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
