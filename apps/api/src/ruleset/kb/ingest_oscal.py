from __future__ import annotations

import json
from uuid import UUID

from pydantic import BaseModel, Field, JsonValue
from sqlalchemy import Engine, text


class OscalPart(BaseModel):
    """A statement part, including nested OSCAL prose."""

    name: str
    prose: str | None = None
    parts: list[OscalPart] = Field(default_factory=list)


class OscalControl(BaseModel):
    """The OSCAL fields required for control ingestion."""

    id: str
    uuid: UUID | None = None
    title: str
    params: list[dict[str, JsonValue]] = Field(default_factory=list)
    parts: list[OscalPart] = Field(default_factory=list)
    controls: list[OscalControl] = Field(default_factory=list)


class OscalGroup(BaseModel):
    """A recursively nested OSCAL control group."""

    controls: list[OscalControl] = Field(default_factory=list)
    groups: list[OscalGroup] = Field(default_factory=list)


class OscalMetadata(BaseModel):
    """Catalog identity fields used to version a framework."""

    title: str
    version: str


class OscalCatalog(BaseModel):
    """The supported subset of an OSCAL catalog."""

    metadata: OscalMetadata
    controls: list[OscalControl] = Field(default_factory=list)
    groups: list[OscalGroup] = Field(default_factory=list)


class OscalDocument(BaseModel):
    """Top-level OSCAL catalog document."""

    catalog: OscalCatalog


def parse_oscal(payload: str | bytes) -> OscalDocument:
    """Validate an OSCAL JSON catalog before it reaches persistence code."""
    return OscalDocument.model_validate_json(payload)


def _group_controls(group: OscalGroup) -> list[OscalControl]:
    return group.controls + [control for child in group.groups for control in _group_controls(child)]


def _statement_text(parts: list[OscalPart]) -> str:
    lines = [part.prose for part in parts if part.name == "statement" and part.prose]
    lines.extend(_statement_text(part.parts) for part in parts if part.parts)
    return "\n".join(line for line in lines if line)


def _flatten(controls: list[OscalControl]) -> list[OscalControl]:
    return [control for root in controls for control in [root, *_flatten(root.controls)]]


def ingest_oscal(
    document: OscalDocument,
    engine: Engine,
    *,
    framework_name: str,
    publisher: str,
    source_url: str,
) -> int:
    """Upsert one validated OSCAL catalog and return its control count."""
    catalog = document.catalog
    roots = catalog.controls + [control for group in catalog.groups for control in _group_controls(group)]
    controls = _flatten(roots)

    with engine.begin() as connection:
        framework_id = connection.execute(
            text(
                "INSERT INTO frameworks (name, version, publisher, machine_readable_source) "
                "VALUES (:name, :version, :publisher, :source) "
                "ON CONFLICT (name, version) DO UPDATE SET publisher = EXCLUDED.publisher, "
                "machine_readable_source = EXCLUDED.machine_readable_source RETURNING id"
            ),
            {"name": framework_name, "version": catalog.metadata.version, "publisher": publisher, "source": source_url},
        ).scalar_one()
        statement = text(
            "INSERT INTO controls "
            "(framework_id, control_code, title, description, params, oscal_uuid) "
            "VALUES (:framework_id, :code, :title, :description, CAST(:params AS jsonb), :uuid) "
            "ON CONFLICT (framework_id, control_code) DO UPDATE SET title = EXCLUDED.title, "
            "description = EXCLUDED.description, params = EXCLUDED.params, "
            "oscal_uuid = EXCLUDED.oscal_uuid"
        )
        connection.execute(
            statement,
            [
                {
                    "framework_id": framework_id,
                    "code": control.id.upper(),
                    "title": control.title,
                    "description": _statement_text(control.parts),
                    "params": json.dumps(control.params),
                    "uuid": control.uuid,
                }
                for control in controls
            ],
        )
    return len(controls)
