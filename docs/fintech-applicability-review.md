# Fintech applicability review package

Status: **candidate only — not loaded by the application**. Activating these rules requires the
repository's human-reviewed ruleset process. Scope signals are user attestations, not legal advice.

The [machine-validated activation manifest](fintech-activation-manifest.json) records the source
review, classification, mandatory approvals, minimum 30-profile evaluation set, and authenticated
browser gate for every regime. GLBA is the first reviewer-ready example, with a
[32-profile candidate set](../apps/api/tests/evals/glba-golden-candidates.json) and shared workflow
contract; neither artifact is loaded as production legal logic.

| Candidate | Proposed deterministic condition | Classification | Primary authority | Review caveat |
| --- | --- | --- | --- | --- |
| GLBA Safeguards Rule | `ftc_financial_institution`, `handles_customer_financial_information`, and no other section 505 regulator | US federal regulation | [FTC, 16 CFR Part 314](https://www.ftc.gov/business-guidance/resources/ftc-safeguards-rule-what-your-business-needs-know) | Detailed candidate facts and requirement-level work are recorded in the [GLBA source review](glba-safeguards-source-review.md). The fewer-than-5,000-consumer treatment is not a blanket exemption. |
| PCI DSS 4.0.1 | Explicit assurance objective plus direct account-data or CDE-impact facts | Contractual industry standard | [PCI SSC document library](https://www.pcisecuritystandards.org/document_library/) | Detailed role, outsourcing, CDE, and validation facts are recorded in the [PCI DSS source review](pci-dss-source-review.md). It is never activated as a legal determination. |
| Regulation S-P | `reg_sp_covered_institution` | US federal securities rule | [SEC final rule](https://www.sec.gov/rules-regulations/2024/06/s7-05-23) | Covered categories include broker-dealers, investment companies, registered advisers, funding portals, and transfer agents. The amended-rule compliance dates were 3 December 2025 for larger entities and 3 June 2026 for smaller entities. |
| FINRA Rule 4370 | `finra_member` | SRO rule | [FINRA BCP guidance](https://www.finra.org/rules-guidance/key-topics/business-continuity-planning) | Applicability is membership-based; the plan must be tailored to the firm's business. |
| NYDFS Part 500 | `nydfs_licensed` | New York regulation | [NYDFS Cybersecurity Resource Center](https://www.dfs.ny.gov/industry_guidance/cybersecurity) | Record limited exemptions and Class A status before deriving individual obligations. |
| SOX Section 404 | `exchange_act_reporting_company` | Reporting/audit requirement | [SEC Section 404 rule](https://www.sec.gov/rules-regulations/2003/03/managements-report-internal-control-over-financial-reporting-certification-disclosure-exchange-act) | Do not substitute the broader `public_company` signal; filer status affects auditor-attestation requirements. |
| CCPA/CPRA | `ccpa_covered_business` and `california_consumer_data` | California privacy law | [CPPA applicability FAQ](https://cppa.ca.gov/faq) | The attestation must account for current revenue/data/revenue-share thresholds, related entities, and exemptions. |
| DORA | `eu_financial_entity` | EU regulation | [Regulation (EU) 2022/2554, Article 2](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022R2554) | Confirm the Article 2 entity category and exclusions; ICT providers have a distinct treatment. |
| MAS TRM Notice | `mas_trm_notice_subject` | Singapore regulatory notice | [MAS Notice on TRM FAQ](https://www.mas.gov.sg/-/media/mas-media-library/regulation/faqs/trpd/faqs---notice-on-technology-risk-management/faqs---notice-on-trm/faq---notice-on-technology-risk-management.pdf) | Store the exact applicable notice number (for example FSM-N05 for banks) before activating obligation-level rules. |

## Activation checklist

1. Compliance reviewer confirms each condition, citation, exclusions, and effective date.
2. Replace broad booleans with regulator/entity subtype facts where the review requires them.
3. Add the approved versioned ruleset through a dedicated reviewed pull request.
4. Turn the candidate profiles in `apps/api/tests/evals/fintech-applicability-candidates.json`
   into active precision/recall cases.
5. Add only publisher- or SCF-sourced control mappings; never infer mappings from similar wording.
