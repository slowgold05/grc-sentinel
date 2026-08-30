from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from ruleset.config import settings
from ruleset.generation.faithfulness import FaithfulnessVerdict
from ruleset.generation.models import CitationVerdict, GeneratedStatement, GenerationOutput
from ruleset.generation.store import record_model_usage, store_policy


def test_stores_only_citation_verified_policy_and_usage() -> None:
    engine = create_engine(str(settings.database_url))
    org_id, engagement_id = uuid4(), uuid4()
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        connection.execute(text("INSERT INTO orgs (id, name) VALUES (:id, 'generation')"), {"id": org_id})
        connection.execute(
            text(
                "INSERT INTO engagements (id, org_id, company, expires_at) "
                "VALUES (:id, :org, '{}', :expires)"
            ),
            {"id": engagement_id, "org": org_id, "expires": datetime.now(UTC) + timedelta(days=1)},
        )
    output = GenerationOutput(
        statements=[GeneratedStatement(text="Use MFA.", control_ids=["IA-2"])]
    )
    try:
        with pytest.raises(ValueError, match="invalid control"):
            store_policy(
                engine,
                org_id,
                engagement_id,
                "access-control",
                "Authentication",
                output,
                CitationVerdict(accepted=False, invalid_control_ids=["IA-2"]),
                [FaithfulnessVerdict(faithful=True, issue="")],
            )
        policy_id = store_policy(
            engine,
            org_id,
            engagement_id,
            "access-control",
            "Authentication",
            output,
            CitationVerdict(accepted=True, invalid_control_ids=[]),
            [FaithfulnessVerdict(faithful=True, issue="")],
        )
        record_model_usage(
            engine,
            org_id,
            engagement_id,
            provider="test",
            model="test-model",
            input_tokens=10,
            output_tokens=5,
            cost_microusd=20,
        )
        with engine.begin() as connection:
            connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
            assert connection.execute(
                text("SELECT count(*) FROM statements WHERE policy_id = :id"), {"id": policy_id}
            ).scalar_one() == 1
            assert connection.execute(text("SELECT sum(cost_microusd) FROM model_usage")).scalar_one() == 20
    finally:
        with engine.begin() as connection:
            connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
