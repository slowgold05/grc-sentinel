import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from ruleset.rules.engine import evaluate, evaluate_scope
from ruleset.rules.models import CompanyFacts, Rule


HIPAA = Rule.model_validate(
    {
        "rule_id": "hipaa-covered-entity-v2",
        "regulation": "HIPAA",
        "all": [
            {"fact": "data_types", "op": "includes", "value": "phi"},
            {"fact": "geos", "op": "includes", "value": "us"},
        ],
        "explanation": "Handles PHI for US persons",
        "citations": ["45 CFR §164.302"],
        "version": 2,
    }
)


def test_matching_rule_returns_auditable_determination() -> None:
    facts = CompanyFacts({"data_types": ["phi"], "geos": ["us"]})
    result = evaluate(facts, [HIPAA])
    assert result[0].rule_id == "hipaa-covered-entity-v2"
    assert result[0].facts == facts.root


@pytest.mark.parametrize(
    "facts",
    [
        {"data_types": [], "geos": ["us"]},
        {"data_types": ["phi"], "geos": []},
        {"data_types": ["phi"]},
    ],
)
def test_rule_requires_every_fact(facts: dict[str, list[str]]) -> None:
    assert evaluate(CompanyFacts(facts), [HIPAA]) == []


def test_missing_fact_requires_review_but_false_fact_is_not_applicable() -> None:
    missing = evaluate_scope(CompanyFacts({"data_types": ["phi"]}), [HIPAA])[0]
    disproved = evaluate_scope(
        CompanyFacts({"data_types": ["pii"], "geos": ["us"]}), [HIPAA]
    )[0]

    assert missing.status == "needs_review"
    assert missing.missing_facts == ["geos"]
    assert disproved.status == "not_applicable"
    assert disproved.missing_facts == []


def test_classification_flows_into_determination() -> None:
    rule = Rule.model_validate(
        {**HIPAA.model_dump(by_alias=True), "classification": "sro_rule"}
    )
    result = evaluate(CompanyFacts({"data_types": ["phi"], "geos": ["us"]}), [rule])

    assert result[0].classification == "sro_rule"


def test_numeric_comparison_requires_numbers() -> None:
    rule = Rule.model_validate(
        {
            **HIPAA.model_dump(by_alias=True),
            "all": [{"fact": "employees", "op": "gte", "value": 50}],
        }
    )
    assert evaluate(CompanyFacts({"employees": 50}), [rule])
    assert not evaluate(CompanyFacts({"employees": "50"}), [rule])


def test_unknown_operation_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Rule.model_validate(
            {
                **HIPAA.model_dump(by_alias=True),
                "all": [{"fact": "x", "op": "contains", "value": "y"}],
            }
        )


@given(st.sets(st.sampled_from(["phi", "pii"])), st.sets(st.sampled_from(["us", "sg"])))
def test_hipaa_fires_exactly_for_phi_and_us(data_types: set[str], geos: set[str]) -> None:
    facts = CompanyFacts({"data_types": sorted(data_types), "geos": sorted(geos)})
    assert bool(evaluate(facts, [HIPAA])) == ("phi" in data_types and "us" in geos)
