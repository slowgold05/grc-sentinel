from typing import TypeGuard

from pydantic import JsonValue

from ruleset.rules.models import CompanyFacts, Condition, Determination, Rule


def _number(value: JsonValue) -> TypeGuard[int | float]:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _matches(actual: JsonValue, condition: Condition) -> bool:
    if condition.op == "equals":
        return actual == condition.value
    if condition.op == "includes":
        return isinstance(actual, list) and condition.value in actual
    if not _number(actual) or not _number(condition.value):
        return False
    return actual >= condition.value if condition.op == "gte" else actual <= condition.value


def evaluate(facts: CompanyFacts, rules: list[Rule]) -> list[Determination]:
    """Return determinations for rules whose conditions all match the facts."""
    snapshot = facts.model_dump()
    return [
        Determination(
            rule_id=rule.rule_id,
            rule_version=rule.version,
            regulation=rule.regulation,
            explanation=rule.explanation,
            citations=rule.citations,
            facts=snapshot,
        )
        for rule in rules
        if all(
            condition.fact in snapshot and _matches(snapshot[condition.fact], condition)
            for condition in rule.all_conditions
        )
    ]

