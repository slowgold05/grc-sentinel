from pathlib import Path

from pydantic import TypeAdapter

from ruleset.rules.models import Rule

_RULES = TypeAdapter(list[Rule])


def load_rules(path: Path) -> list[Rule]:
    """Load and validate a versioned JSON ruleset."""
    return _RULES.validate_json(path.read_bytes())

