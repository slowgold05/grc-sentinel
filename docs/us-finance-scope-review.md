# US securities and New York finance scope review

Status: **detailed candidate scope model — active rulesets still require human review**

## Regulation S-P

Primary authority: [SEC final rule](https://www.sec.gov/rules-regulations/2024/06/s7-05-23)
and [small-entity compliance guide](https://www.sec.gov/file/regulation-s-p-small-entity-compliance-guide).

The intake separately records covered-institution status, entity category, larger/smaller cohort,
customer-information handling, and service-provider use. Covered categories represented by the
model are broker-dealers, investment companies, SEC-registered investment advisers, funding
portals, and transfer agents. `other` cannot create an automatic positive result.

The 2024 amendment's cohort dates are retained as source-version metadata, not used to imply that
one cohort is outside Regulation S-P. Requirement ingestion must distinguish privacy notices,
safeguards, disposal, incident response, service-provider oversight, records, and individual
notification rather than reducing the regulation to a generic breach rule.

## FINRA Rule 4370

Primary authority: [FINRA Rule 4370](https://www.finra.org/rules-guidance/rulebooks/finra-rules/4370).

FINRA membership is the scope fact. Firm type, customer accounts, identified mission-critical
systems, and confirmed BCP scope are readiness facts used to tailor the requirement and evidence
plan; they do not decide whether a member may ignore the rule. The product must preserve FINRA's
SRO classification and must not present Rule 4370 as federal legislation.

Requirement ingestion must retain rule subsection identifiers and cover the written plan, material
change updates, annual review, senior-management responsibility, customer disclosure, emergency
contacts, and business-specific plan elements. Cybersecurity mappings must be publisher- or
SCF-sourced, not inferred from business-continuity wording.

## 23 NYCRR Part 500

Primary authority: [NYDFS Cybersecurity Resource Center](https://www.dfs.ny.gov/industry_guidance/cybersecurity)
and [current Part 500 text](https://www.dfs.ny.gov/industry_guidance/cybersecurity/23_nycrr_part_500).

The intake records covered-entity status, authorization family, exact §500.19 exemption claim,
Class A status, and use of an affiliate cybersecurity program. A limited exemption does not erase
covered-entity status; it changes the applicable requirement set. `not_determined` must remain a
review state.

Requirement ingestion must version the amended Part 500 text and apply exemptions at the section
level. Class A and affiliate-program facts must modify only the requirements supported by the
official text. The platform must not calculate legal exemption eligibility from incomplete revenue,
asset, employee, affiliate, or New York nexus data.

## Shared activation gate

- Compliance review approves every entity category, exclusion, exemption, cohort, and citation.
- Candidate profiles cover positive, negative, missing, boundary, exemption, and mixed-regime cases.
- Requirement identifiers and text come from the issuing authority; mappings come from the
  authority or SCF.
- Regulation S-P and NYDFS create regulatory determinations; FINRA creates an SRO-rule
  determination. None activates from readiness facts alone.
- Coverage, gaps, policies, exports, and Audit Hub retain the source version and exact scope facts.
