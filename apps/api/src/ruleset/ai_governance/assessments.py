import json
from uuid import UUID

from sqlalchemy import Engine, text

from ruleset.ai_governance.models import AIImpactContent, AIImpactDraft, AIImpactVersion

_SOURCES = {"internal_ai_risk": "1", "nist_ai_rmf": "1.0", "iso_42001": "2023"}


def _clean(row: object, model: type[AIImpactDraft] | type[AIImpactVersion]):
    values = dict(row)
    values.pop("org_id")
    values.pop("engagement_id")
    return model.model_validate(values)


def save_impact_draft(engine: Engine, org_id: UUID, system_id: UUID, author: str, content: AIImpactContent) -> AIImpactDraft:
    """Create or replace the current editable assessment draft."""
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        engagement_id = connection.execute(text("SELECT engagement_id FROM ai_systems WHERE id = :id"), {"id": system_id}).scalar_one_or_none()
        if engagement_id is None:
            raise LookupError("AI system not found")
        row = connection.execute(text("INSERT INTO ai_impact_assessment_drafts (org_id, engagement_id, ai_system_id, content, author) VALUES (:org_id, :engagement_id, :system_id, CAST(:content AS jsonb), :author) ON CONFLICT (ai_system_id) DO UPDATE SET content = EXCLUDED.content, author = EXCLUDED.author, updated_at = now() RETURNING *"), {"org_id": org_id, "engagement_id": engagement_id, "system_id": system_id, "content": json.dumps(content.model_dump()), "author": author}).mappings().one()
        return _clean(row, AIImpactDraft)


def submit_impact_assessment(engine: Engine, org_id: UUID, system_id: UUID, author: str) -> AIImpactVersion:
    """Copy the current draft into a new append-only numbered version."""
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        draft = connection.execute(text("SELECT * FROM ai_impact_assessment_drafts WHERE ai_system_id = :id"), {"id": system_id}).mappings().one_or_none()
        if draft is None:
            raise LookupError("impact assessment draft not found")
        content = AIImpactContent.model_validate(draft["content"])
        missing = [name for name, value in content.model_dump().items() if not value.strip()]
        version = connection.execute(text("SELECT COALESCE(max(version), 0) + 1 FROM ai_impact_assessment_versions WHERE ai_system_id = :id"), {"id": system_id}).scalar_one()
        row = connection.execute(text("INSERT INTO ai_impact_assessment_versions (org_id, engagement_id, ai_system_id, version, content, status, missing_facts, author, source_versions) VALUES (:org_id, :engagement_id, :system_id, :version, CAST(:content AS jsonb), :status, CAST(:missing AS jsonb), :author, CAST(:sources AS jsonb)) RETURNING *"), {"org_id": org_id, "engagement_id": draft["engagement_id"], "system_id": system_id, "version": version, "content": json.dumps(content.model_dump()), "status": "needs_review" if missing else "complete", "missing": json.dumps(missing), "author": author, "sources": json.dumps(_SOURCES)}).mappings().one()
        return _clean(row, AIImpactVersion)


def list_impact_versions(engine: Engine, org_id: UUID, system_id: UUID) -> list[AIImpactVersion]:
    """List immutable submitted versions visible to the tenant."""
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        rows = connection.execute(text("SELECT * FROM ai_impact_assessment_versions WHERE ai_system_id = :id ORDER BY version DESC"), {"id": system_id}).mappings()
        return [_clean(row, AIImpactVersion) for row in rows]
