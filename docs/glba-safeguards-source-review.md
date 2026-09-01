# GLBA Safeguards Rule source review

Status: **candidate scope model — not an active application ruleset**

This artifact records the source basis for the GLBA intake and evaluation candidates. It does not
constitute legal advice or approval to activate `rulesets/*.json`.

## Source identity

| Field | Value |
| --- | --- |
| Regime | FTC Standards for Safeguarding Customer Information |
| Citation | 16 CFR Part 314 |
| Classification | US federal regulation |
| Publisher | Federal Trade Commission |
| Current rule hub | <https://www.ftc.gov/legal-library/browse/rules/safeguards-rule> |
| Small-entity compliance guide | <https://www.ftc.gov/business-guidance/resources/ftc-safeguards-rule-what-your-business-needs-know> |
| Notification amendment | <https://www.ftc.gov/news-events/news/press-releases/2023/10/ftc-amends-safeguards-rule-require-non-banking-financial-institutions-report-data-security-breaches> |
| Repository review date | 2026-09-01 |

The rule text is the authority. FTC guidance explains that scope concerns financial institutions
under FTC jurisdiction that are not under another GLBA section 505 regulator's enforcement
authority. The entity's activities matter; its marketing label does not establish scope.

## Intake facts and meaning

| Fact | Meaning | Unknown behavior |
| --- | --- | --- |
| `ftc_financial_institution` | Reviewed conclusion that activities place the entity within the FTC Rule's financial-institution definition | `needs_review` |
| `glba_financial_activity` | Activity category supporting that conclusion; `other_financial_activity` always needs specialist review | Does not independently activate scope |
| `handles_customer_financial_information` | Entity maintains customer information within the reviewed Rule definition | `needs_review` |
| `glba_section_505_other_regulator` | Another regulator has GLBA section 505 enforcement authority over the institution | `needs_review`; `true` disproves the FTC candidate, not GLBA obligations under another regulator |
| `glba_customer_count` | Number of consumers whose customer information is maintained | Used to scope specified provisions; never a blanket applicability exemption |

The enumerated financial activities mirror examples in FTC guidance and are not exhaustive.
`other_financial_activity` must not be converted into an automatic positive result.

## Candidate decision boundary

The candidate FTC rule requires all three reviewed facts:

1. `ftc_financial_institution = true`
2. `handles_customer_financial_information = true`
3. `glba_section_505_other_regulator = false`

A missing fact produces `needs_review`. A known false scope fact produces `not_applicable` for the
FTC Safeguards Rule candidate. That result must not be generalized to every GLBA regulator.

Institutions maintaining customer information concerning fewer than 5,000 consumers may be
excepted from specified requirements identified by the Rule. The platform must apply that fact at
the requirement level after source review; it must not suppress the overall determination.

## Requirement ingestion still required before activation

- Create a reviewer-approved structured artifact for §§ 314.3 and 314.4, preserving subsection
  identifiers, effective dates, and the official source URL.
- Represent the fewer-than-5,000-consumer treatment at the individual requirement level.
- Represent § 314.4(j) notification-event conditions separately from general incident response;
  do not describe every security event as reportable.
- Import only FTC- or SCF-sourced mappings. Leave unsupported requirements unmapped.
- Add positive, negative, other-regulator, unknown, small-institution, activity-boundary, and
  notification-event golden profiles for human approval.
- Activate the versioned JSON ruleset only in the protected human-reviewed ruleset process.

## Reviewer package

- Candidate rule: `apps/api/tests/evals/glba-candidate-rule.json`
- Candidate golden set: `apps/api/tests/evals/glba-golden-candidates.json`
- Automated integrity check: `apps/api/tests/evals/test_glba_candidate_set.py`

The candidate set contains 32 positive, negative, boundary, and unknown profiles. Passing the
test proves only that the proposed decision boundary is deterministic; it does not constitute
legal approval. Before activation, a qualified reviewer must approve the source version, each
condition and citation, the treatment of `other_financial_activity`, and every expected result.
