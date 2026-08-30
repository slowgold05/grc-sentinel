from uuid import UUID

from pydantic import BaseModel, JsonValue
from sqlalchemy import Engine, text


class ControlSnapshot(BaseModel):
    """Comparable control content from one framework version."""

    code: str
    title: str
    description: str
    params: dict[str, JsonValue]


class FrameworkDrift(BaseModel):
    """Control codes added, removed, or materially changed between versions."""

    added: list[str]
    removed: list[str]
    changed: list[str]

    @property
    def affected_codes(self) -> list[str]:
        """Return every control code requiring review."""
        return sorted({*self.added, *self.removed, *self.changed})


class AffectedStatement(BaseModel):
    """Tenant-visible policy statement citing a changed control."""

    statement_id: UUID
    policy_id: UUID
    text: str
    control_ids: list[str]


def diff_controls(old: list[ControlSnapshot], new: list[ControlSnapshot]) -> FrameworkDrift:
    """Compare versions by stable control code and substantive content."""
    old_by_code = {control.code: control for control in old}
    new_by_code = {control.code: control for control in new}
    shared = old_by_code.keys() & new_by_code.keys()
    return FrameworkDrift(
        added=sorted(new_by_code.keys() - old_by_code.keys()),
        removed=sorted(old_by_code.keys() - new_by_code.keys()),
        changed=sorted(
            code
            for code in shared
            if old_by_code[code].model_dump(exclude={"code"})
            != new_by_code[code].model_dump(exclude={"code"})
        ),
    )


def compare_frameworks(engine: Engine, old_framework_id: UUID, new_framework_id: UUID) -> FrameworkDrift:
    """Load and compare two versions of the same named framework."""
    with engine.connect() as connection:
        frameworks = list(connection.execute(
            text("SELECT id, name FROM frameworks WHERE id IN (:old, :new)"),
            {"old": old_framework_id, "new": new_framework_id},
        ).mappings())
        if len(frameworks) != 2 or len({row["name"] for row in frameworks}) != 1:
            raise ValueError("framework versions must exist and have the same name")
        rows = connection.execute(
            text(
                "SELECT framework_id, control_code AS code, title, description, params "
                "FROM controls WHERE framework_id IN (:old, :new)"
            ),
            {"old": old_framework_id, "new": new_framework_id},
        ).mappings()
        snapshots = [(row["framework_id"], ControlSnapshot.model_validate(row)) for row in rows]
    return diff_controls(
        [control for framework_id, control in snapshots if framework_id == old_framework_id],
        [control for framework_id, control in snapshots if framework_id == new_framework_id],
    )


def find_affected_statements(
    engine: Engine, org_id: UUID, control_codes: list[str]
) -> list[AffectedStatement]:
    """Find tenant-visible statements citing any drifted control code."""
    if not control_codes:
        return []
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        rows = connection.execute(
            text(
                "SELECT id AS statement_id, policy_id, text, control_ids FROM statements "
                "WHERE control_ids && CAST(:codes AS text[]) ORDER BY id"
            ),
            {"codes": control_codes},
        ).mappings()
        return [AffectedStatement.model_validate(row) for row in rows]
