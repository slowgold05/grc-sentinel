from ruleset.rules.engine import evaluate_scope
from ruleset.rules.models import CompanyFacts, Rule


GLBA_CANDIDATE = Rule.model_validate(
    {
        "rule_id": "glba-ftc-safeguards-candidate-v1",
        "regulation": "GLBA Safeguards Rule",
        "classification": "regulation",
        "all": [
            {"fact": "ftc_financial_institution", "op": "equals", "value": True},
            {
                "fact": "handles_customer_financial_information",
                "op": "equals",
                "value": True,
            },
            {
                "fact": "glba_section_505_other_regulator",
                "op": "equals",
                "value": False,
            },
        ],
        "explanation": "Candidate only; requires reviewer approval before activation.",
        "citations": ["16 CFR §§ 314.1(b), 314.2"],
        "version": 1,
    }
)


def test_glba_candidate_distinguishes_scope_boundaries() -> None:
    applicable = evaluate_scope(
        CompanyFacts(
            {
                "ftc_financial_institution": True,
                "handles_customer_financial_information": True,
                "glba_section_505_other_regulator": False,
                "glba_customer_count": 12000,
            }
        ),
        [GLBA_CANDIDATE],
    )[0]
    unknown = evaluate_scope(
        CompanyFacts(
            {
                "ftc_financial_institution": True,
                "handles_customer_financial_information": True,
            }
        ),
        [GLBA_CANDIDATE],
    )[0]
    other_regulator = evaluate_scope(
        CompanyFacts(
            {
                "ftc_financial_institution": True,
                "handles_customer_financial_information": True,
                "glba_section_505_other_regulator": True,
            }
        ),
        [GLBA_CANDIDATE],
    )[0]

    assert applicable.status == "applicable"
    assert unknown.status == "needs_review"
    assert unknown.missing_facts == ["glba_section_505_other_regulator"]
    assert other_regulator.status == "not_applicable"


def test_small_institution_relief_does_not_erase_candidate_scope() -> None:
    result = evaluate_scope(
        CompanyFacts(
            {
                "ftc_financial_institution": True,
                "handles_customer_financial_information": True,
                "glba_section_505_other_regulator": False,
                "glba_customer_count": 4999,
            }
        ),
        [GLBA_CANDIDATE],
    )[0]

    assert result.status == "applicable"
