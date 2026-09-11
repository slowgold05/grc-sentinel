import json

from sqlalchemy import text

from ruleset import database
from ruleset.kb import ingest_nist_ai_rmf as importer


def test_imports_nist_ai_rmf_idempotently(monkeypatch) -> None:
    monkeypatch.setattr(importer, "FRAMEWORK_VERSION", "test-only")
    payload = json.dumps(
        [
            {
                "type": "Govern",
                "title": "GOVERN 1.1",
                "category": "GOVERN-1",
                "description": "Test outcome text.",
                "section_actions": "Test suggested action.",
                "AI Actors": ["Governance and Oversight"],
                "Topic": ["Governance"],
            }
        ]
    )
    document = importer.parse_nist_ai_rmf(payload)

    assert importer.ingest_nist_ai_rmf(document, database.engine) == 1
    assert importer.ingest_nist_ai_rmf(document, database.engine) == 1

    with database.engine.begin() as connection:
        row = connection.execute(
            text(
                "SELECT c.control_code, c.description, c.params, f.version, f.publisher "
                "FROM controls c JOIN frameworks f ON f.id = c.framework_id "
                "WHERE f.name = 'NIST AI RMF' AND f.version = 'test-only'"
            ),
        ).mappings().one()
        connection.execute(
            text("DELETE FROM frameworks WHERE name = 'NIST AI RMF' AND version = 'test-only'")
        )
        assert row["control_code"] == "GOVERN 1.1"
        assert row["description"] == "Test outcome text."
        assert row["params"]["guidance_classification"] == "voluntary_playbook_suggestions"
        assert row["version"] == "test-only"
        assert row["publisher"] == "NIST"
