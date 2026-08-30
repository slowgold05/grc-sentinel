from uuid import uuid4

from sqlalchemy import create_engine, text

from ruleset.config import settings
from ruleset.generation.context import plan_policy, retrieve_controls


def test_plans_templates_and_retrieves_exact_controls() -> None:
    engine = create_engine(str(settings.database_url))
    policy_type = f"test-{uuid4()}"
    with engine.begin() as connection:
        control_id = connection.execute(text("SELECT id FROM controls LIMIT 1")).scalar_one()
        connection.execute(
            text(
                "INSERT INTO policy_templates (policy_type, section, template_body, control_ids) "
                "VALUES (:type, 'Access', 'Describe access.', ARRAY[:control]::uuid[])"
            ),
            {"type": policy_type, "control": control_id},
        )
    try:
        plan = plan_policy(engine, policy_type)
        assert plan[0].control_ids == [control_id]
        controls = retrieve_controls(engine, plan[0].control_ids)
        assert controls and controls[0].control_id
        assert controls[0].text
    finally:
        with engine.begin() as connection:
            connection.execute(
                text("DELETE FROM policy_templates WHERE policy_type = :type"), {"type": policy_type}
            )
