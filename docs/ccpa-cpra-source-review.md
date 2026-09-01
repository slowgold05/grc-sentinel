# CCPA / CPRA source review

Status: **detailed candidate scope model — active ruleset requires human review**

## Source identity

| Field | Value |
| --- | --- |
| Regime | California Consumer Privacy Act, as amended by CPRA |
| Classification | California privacy law |
| Authority | California Privacy Protection Agency and California Legislature |
| Official FAQ | <https://cppa.ca.gov/faq> |
| CPI-adjusted thresholds | <https://cppa.ca.gov/regulations/cpi_adjustment.html> |
| 2026 regulations | <https://cppa.ca.gov/regulations/ccpa_updates.html> |
| Repository review date | 2026-09-01 |

## Scope facts

The intake records whether the entity is for-profit, does business in California, determines the
purposes and means of processing, and processes California consumer personal information. It then
stores the threshold year and raw values for gross revenue, consumers/households, and percentage
of revenue from selling or sharing personal information.

The reviewed covered-business conclusion remains a separate nullable fact. It is not automatically
calculated until a human-approved ruleset versions the relevant threshold period, definitions,
related-entity treatment, and exclusions.

For the period effective 1 January 2025, CPPA publishes a CPI-adjusted gross-revenue amount of
$26,625,000. The other business-definition alternatives include 100,000 California consumers or
households and 50% of annual revenue from selling or sharing California residents' personal
information. Those figures must remain attached to their effective period.

## Exemption boundary

The model distinguishes no identified exemption, GLBA-regulated information, CFIPA-regulated
information, HIPAA PHI, nonprofit status, government status, another reviewed exemption, and an
undetermined state. Data-specific exemptions must not be promoted into a claim that every record
held by a financial or healthcare entity is outside the CCPA.

## Activation work remaining

- Reviewer approves business-definition logic, annual threshold versions, related-entity and
  voluntary-certification paths, service-provider/contractor treatment, and statutory exemptions.
- Import stable statute/regulation identifiers with official source version and effective dates.
- Model the 2026 cybersecurity-audit, risk-assessment, ADMT, and insurance regulations only for
  businesses meeting their distinct triggers and implementation dates.
- Add boundary profiles immediately below/at/above each threshold, plus nonprofit, government,
  GLBA-information, related-entity, and missing-fact cases.
- Load only publisher- or SCF-sourced control mappings and expose unmapped obligations.
- Drive approved requirements through coverage, risks, policies, export, and Audit Hub.
