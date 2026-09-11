from __future__ import annotations

import json
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import Engine, text


SOURCE_URL = "https://airc.nist.gov/docs/playbook.json"
FRAMEWORK_NAME = "NIST AI RMF"
FRAMEWORK_VERSION = "1.0"
_OUTCOME_ID = re.compile(r"^(GOVERN|MAP|MEASURE|MANAGE) \d+\.\d+$")


class NistAiRmfOutcome(BaseModel):
    """Publisher fields required from one NIST AI RMF Playbook record."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    function: str = Field(alias="type")
    title: str
    category: str
    description: str = Field(min_length=1)
    suggested_actions: str = Field(alias="section_actions", default="")
    ai_actors: list[str] = Field(alias="AI Actors", default_factory=list)
    topics: list[str] = Field(alias="Topic", default_factory=list)

    @field_validator("title")
    @classmethod
    def validate_outcome_id(cls, value: str) -> str:
        if not _OUTCOME_ID.fullmatch(value):
            raise ValueError("invalid NIST AI RMF outcome identifier")
        return value


class NistAiRmfPlaybook(BaseModel):
    outcomes: list[NistAiRmfOutcome]


def parse_nist_ai_rmf(payload: str | bytes) -> NistAiRmfPlaybook:
    """Validate the official JSON array before persistence."""
    return NistAiRmfPlaybook(outcomes=json.loads(payload))


def ingest_nist_ai_rmf(document: NistAiRmfPlaybook, engine: Engine) -> int:
    """Idempotently import AI RMF outcomes and separately labelled Playbook guidance."""
    with engine.begin() as connection:
        framework_id = connection.execute(
            text(
                "INSERT INTO frameworks (name, version, publisher, machine_readable_source) "
                "VALUES (:name, :version, 'NIST', :source) "
                "ON CONFLICT (name, version) DO UPDATE SET publisher = EXCLUDED.publisher, "
                "machine_readable_source = EXCLUDED.machine_readable_source RETURNING id"
            ),
            {"name": FRAMEWORK_NAME, "version": FRAMEWORK_VERSION, "source": SOURCE_URL},
        ).scalar_one()
        connection.execute(
            text(
                "INSERT INTO controls "
                "(framework_id, control_code, title, description, params) "
                "VALUES (:framework_id, :code, :title, :description, CAST(:params AS jsonb)) "
                "ON CONFLICT (framework_id, control_code) DO UPDATE SET title = EXCLUDED.title, "
                "description = EXCLUDED.description, params = EXCLUDED.params"
            ),
            [
                {
                    "framework_id": framework_id,
                    "code": outcome.title,
                    "title": outcome.description,
                    "description": outcome.description,
                    "params": json.dumps(
                        {
                            "function": outcome.function,
                            "category": outcome.category,
                            "suggested_actions": outcome.suggested_actions,
                            "guidance_classification": "voluntary_playbook_suggestions",
                            "ai_actors": outcome.ai_actors,
                            "topics": outcome.topics,
                        }
                    ),
                }
                for outcome in document.outcomes
            ],
        )
    return len(document.outcomes)
