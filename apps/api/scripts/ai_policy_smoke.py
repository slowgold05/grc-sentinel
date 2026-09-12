"""Run one disposable, fictional AI-policy draft through local Ollama."""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx
from sqlalchemy import text

from ruleset.ai_governance.policy_suite import (
    AIPolicyDraftRequest,
    AIPolicyType,
    generate_ai_policy,
)
from ruleset.config import settings
from ruleset.database import engine
from ruleset.generation.openai_compatible_client import call_model_json


async def main() -> None:
    org_id, engagement_id, system_id = uuid4(), uuid4(), uuid4()
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        connection.execute(
            text("INSERT INTO orgs (id, name) VALUES (:id, 'Fictional smoke test')"), {"id": org_id}
        )
        connection.execute(
            text(
                'INSERT INTO engagements (id, org_id, company, expires_at) VALUES (:id, :org, \'{"company_name":"Fictional Fintech"}\', :expires)'
            ),
            {"id": engagement_id, "org": org_id, "expires": datetime.now(UTC) + timedelta(hours=1)},
        )
        connection.execute(
            text(
                "INSERT INTO ai_systems (id, org_id, engagement_id, name, description, owner_name, business_purpose, profile) VALUES (:id, :org, :engagement, 'Support assistant', 'Fictional local smoke test', 'AI owner', 'Draft support responses', '{}')"
            ),
            {"id": system_id, "org": org_id, "engagement": engagement_id},
        )
        connection.execute(
            text(
                "INSERT INTO ai_assurance_objectives (org_id, engagement_id, ai_system_id, framework, source_version, objective_type, basis, scope, selected_by) VALUES (:org, :engagement, :system, 'nist_ai_rmf', '1.0', 'voluntary', 'company_strategy', 'Fictional assistant', 'local-reviewer')"
            ),
            {"org": org_id, "engagement": engagement_id, "system": system_id},
        )

    async def call(prompt, schema, model, max_tokens):
        return await call_model_json(
            f"/no_think\n{prompt}",
            schema,
            base_url=settings.llm_base_url,
            model=model,
            max_tokens=max_tokens,
            api_key=settings.llm_api_key.get_secret_value() if settings.llm_api_key else None,
        )

    try:
        draft = await generate_ai_policy(
            engine,
            org_id,
            system_id,
            AIPolicyType.GOVERNANCE,
            AIPolicyDraftRequest(control_ids=["GOVERN 1.1"]),
            lambda prompt, schema: call(prompt, schema, settings.llm_generation_model, 2_500),
            lambda prompt, schema: call(prompt, schema, settings.llm_verifier_model, 2_500),
        )
        print({"status": draft.status, "sources": [source.framework for source in draft.sources]})
    except httpx.HTTPStatusError as error:
        print({"model_error": error.response.text[:500]})
        raise
    finally:
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)}
            )
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})


if __name__ == "__main__":
    asyncio.run(main())
