import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from sqlalchemy import text

from ruleset.audit_hub import create_share_link, resolve_share
from ruleset.coverage_store import store_coverage_results
from ruleset.coverage_verifier import CoverageClaim, verify_evidence_quote
from ruleset.database import engine
from ruleset.gap_analysis import list_required_controls
from ruleset.rules.engine import evaluate
from ruleset.rules.models import CompanyFacts, Rule
from ruleset.rules.store import store_determinations


def test_approved_glba_data_can_flow_through_shared_evidence_path() -> None:
    """Prove the workflow contract without installing unapproved GLBA data."""
    fixture = Path(__file__).parent / "evals" / "glba-candidate-rule.json"
    rule = Rule.model_validate_json(fixture.read_text())
    facts = CompanyFacts(
        {
            "ftc_financial_institution": True,
            "handles_customer_financial_information": True,
            "glba_section_505_other_regulator": False,
            "glba_customer_count": 12_000,
        }
    )
    determination = evaluate(facts, [rule])[0]
    org_id, engagement_id, regulation_id = uuid4(), uuid4(), uuid4()
    framework_id, control_id, upload_id = uuid4(), uuid4(), uuid4()
    expires = datetime.now(UTC) + timedelta(days=1)

    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)}
        )
        connection.execute(
            text("INSERT INTO orgs (id, name) VALUES (:id, 'GLBA contract fixture')"),
            {"id": org_id},
        )
        connection.execute(
            text(
                "INSERT INTO engagements (id, org_id, company, expires_at) "
                "VALUES (:id, :org, CAST(:company AS jsonb), :expires)"
            ),
            {
                "id": engagement_id,
                "org": org_id,
                "company": json.dumps(facts.root),
                "expires": expires,
            },
        )
        connection.execute(
            text(
                "INSERT INTO regulations (id, name, jurisdiction, citation) "
                "VALUES (:id, 'GLBA Safeguards Rule', 'test fixture', 'not authoritative')"
            ),
            {"id": regulation_id},
        )
        connection.execute(
            text(
                "INSERT INTO frameworks "
                "(id, name, version, publisher, machine_readable_source) "
                "VALUES (:id, :name, 'fixture', 'test only', 'test only')"
            ),
            {"id": framework_id, "name": f"GLBA fixture {framework_id}"},
        )
        connection.execute(
            text(
                "INSERT INTO controls (id, framework_id, control_code, title, description) "
                "VALUES (:id, :framework, 'GLBA-FIXTURE', 'Fixture', 'Not a legal mapping')"
            ),
            {"id": control_id, "framework": framework_id},
        )
        connection.execute(
            text(
                "INSERT INTO regulation_controls (regulation_id, control_id, obligation_text_ref) "
                "VALUES (:regulation, :control, 'test fixture only')"
            ),
            {"regulation": regulation_id, "control": control_id},
        )
        connection.execute(
            text(
                "INSERT INTO uploads "
                "(id, org_id, engagement_id, filename, media_type, sha256, ciphertext, nonce, "
                "wrapped_key, key_nonce, expires_at) VALUES "
                "(:id, :org, :engagement, 'fixture.pdf', 'application/pdf', :sha, :blob, :blob, "
                ":blob, :blob, :expires)"
            ),
            {
                "id": upload_id,
                "org": org_id,
                "engagement": engagement_id,
                "sha": "0" * 64,
                "blob": b"x",
                "expires": expires,
            },
        )

    try:
        assert store_determinations(engine, org_id, engagement_id, [determination]) == 1
        stored = list_required_controls(engine, org_id, engagement_id)
        assert [item.id for item in stored] == [control_id]
        verified = verify_evidence_quote(
            CoverageClaim(
                control_id=control_id,
                chunk_id=None,
                status="missing",
                evidence_quote="",
                gap="Reviewer-approved GLBA evidence is not attached.",
            ),
            None,
        )
        assert store_coverage_results(
            engine, org_id, engagement_id, upload_id, [verified]
        ) == 1
        token = create_share_link(engine, org_id, engagement_id, expires)
        share = resolve_share(engine, token)
        assert share is not None
        assert share.coverage[0]["control_id"] == control_id
    finally:
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)}
            )
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
            connection.execute(
                text("DELETE FROM regulations WHERE id = :id"), {"id": regulation_id}
            )
            connection.execute(
                text("DELETE FROM frameworks WHERE id = :id"), {"id": framework_id}
            )
