from typing import TypeGuard

from pydantic import JsonValue

from ruleset.rules.models import CompanyFacts, Condition, Determination, Rule, ScopeEvaluation


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


def evaluate_scope(facts: CompanyFacts, rules: list[Rule]) -> list[ScopeEvaluation]:
    """Classify each rule as applicable, disproved, or missing required facts."""
    snapshot = facts.model_dump()
    results = []
    for rule in rules:
        missing = [
            condition.fact
            for condition in rule.all_conditions
            if condition.fact not in snapshot
        ]
        determination = None
        if not missing and all(
            _matches(snapshot[condition.fact], condition)
            for condition in rule.all_conditions
        ):
            determination = Determination(
                rule_id=rule.rule_id,
                rule_version=rule.version,
                regulation=rule.regulation,
                explanation=rule.explanation,
                citations=rule.citations,
                facts=snapshot,
                classification=rule.classification,
            )
        results.append(
            ScopeEvaluation(
                rule_id=rule.rule_id,
                regulation=rule.regulation,
                classification=rule.classification,
                status=(
                    "needs_review"
                    if missing
                    else "applicable"
                    if determination
                    else "not_applicable"
                ),
                missing_facts=missing,
                determination=determination,
            )
        )
    return results


def evaluate(facts: CompanyFacts, rules: list[Rule]) -> list[Determination]:
    """Return applicable determinations while preserving the established API."""
    return [
        result.determination
        for result in evaluate_scope(facts, rules)
        if result.determination is not None
    ]
