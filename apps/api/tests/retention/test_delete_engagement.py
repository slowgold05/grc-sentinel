from datetime import UTC, datetime, timedelta
from uuid import uuid4

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import create_engine, text

from ruleset.config import settings
from ruleset.retention.delete_engagement import delete_engagement
from ruleset.rules.models import Determination
from ruleset.rules.store import store_determinations
from ruleset.uploads.chunks import store_sections
from ruleset.uploads.parse_worker import DocumentSection, ParsedDocument
from ruleset.uploads.store import store_upload
from ruleset.uploads.validation import validate_upload


def test_hard_delete_leaves_no_engagement_artifacts() -> None:
    engine = create_engine(str(settings.database_url))
    admin_engine = create_engine(str(settings.migration_database_url))
    org_id, engagement_id = uuid4(), uuid4()
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        framework_id = connection.execute(
            text("SELECT id FROM frameworks WHERE name = 'ISO 27001'")
        ).scalar_one()
        connection.execute(text("INSERT INTO orgs (id, name) VALUES (:id, 'test')"), {"id": org_id})
        connection.execute(
            text(
                "INSERT INTO engagements (id, org_id, company, expires_at) "
                "VALUES (:id, :org_id, '{}', :expires_at)"
            ),
            {
                "id": engagement_id,
                "org_id": org_id,
                "expires_at": datetime.now(UTC) + timedelta(days=1),
            },
        )
        connection.execute(
            text(
                "INSERT INTO assurance_objectives "
                "(org_id, engagement_id, framework_id, basis, selected_by) "
                "VALUES (:org_id, :engagement_id, :framework_id, 'company_strategy', 'test-user')"
            ),
            {"org_id": org_id, "engagement_id": engagement_id, "framework_id": framework_id},
        )
    determination = Determination(
        rule_id="hipaa-covered-entity-v2",
        rule_version=2,
        regulation="HIPAA",
        explanation="Handles PHI",
        citations=["45 CFR §164.302"],
        facts={"data_types": ["phi"]},
    )
    store_determinations(engine, org_id, engagement_id, [determination])
    content = b"%PDF-1.7\npolicy\n%%EOF"
    upload_id = store_upload(
        engine,
        org_id,
        engagement_id,
        validate_upload("policy.pdf", content),
        content,
        AESGCM.generate_key(bit_length=256),
    )
    store_sections(
        engine,
        org_id,
        upload_id,
        ParsedDocument(sections=[DocumentSection(seq=1, text="policy")]),
    )

    try:
        assert delete_engagement(engine, org_id, engagement_id)
        with admin_engine.connect() as connection:
            counts = connection.execute(
                text(
                    "SELECT (SELECT count(*) FROM engagements WHERE org_id = :org_id), "
                    "(SELECT count(*) FROM determinations WHERE org_id = :org_id), "
                    "(SELECT count(*) FROM uploads WHERE org_id = :org_id), "
                    "(SELECT count(*) FROM upload_chunks WHERE org_id = :org_id), "
                    "(SELECT count(*) FROM assurance_objectives WHERE org_id = :org_id)"
                ),
                {"org_id": org_id},
            ).one()
        assert tuple(counts) == (0, 0, 0, 0, 0)
    finally:
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
            )
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
