# Fintech full implementation roadmap

Status: **planned — legal activation requires human review**

This roadmap closes the gap between scope-capture demo cards and end-to-end, source-backed
features. “Complete” means more than adding a rule: the product must collect sufficient facts,
make a deterministic and reviewable classification, load sourced requirements and control
mappings, drive coverage and policy workflows, and prove the result with boundary-focused tests.

## Modeling boundary

Do not force every item into the legal-applicability engine.

| Track | Items | Product result |
| --- | --- | --- |
| Legal/regulatory determination | GLBA Safeguards Rule, Regulation S-P, 23 NYCRR Part 500, CCPA/CPRA, DORA, applicable MAS TRM Notice | Immutable determination containing the approved rule version, citations, and exact fact snapshot |
| SRO obligation | FINRA Rule 4370 | Membership-based determination, clearly labeled as an SRO rule rather than legislation |
| Reporting/audit objective | SOX Section 404 | ICFR objective and requirement set; filer and attestation status remain explicit |
| Contractual industry standard | PCI DSS 4.0.1 | Explicitly confirmed assurance objective, scoped requirement set, and validation path; never described as a law |

The LLM must not decide scope, exemptions, mappings, or requirement applicability.

## Definition of done for every regime

1. A reviewer-approved source record identifies publisher, version/effective date, canonical URL,
   covered entities, exclusions, exemptions, and transition rules.
2. Intake collects the minimum facts needed to distinguish positive, negative, exempt, and
   unknown cases. A broad checkbox is not sufficient where the authority distinguishes subtypes.
3. A versioned deterministic rule or objective classifier consumes only those facts and records
   its citations and fact snapshot.
4. Requirements are imported from an authoritative machine-readable source when available.
   Otherwise, a reviewed structured artifact records identifiers and provenance. No AI-recalled
   requirement text is permitted.
5. Control mappings come only from the publisher or SCF. Unmapped requirements remain visibly
   unmapped; semantic similarity cannot create a crosswalk.
6. Required controls flow through retrieval, coverage, gaps, risks, policy generation, export,
   and Audit Hub without bypassing citation verification or tenant isolation.
7. The golden set contains positive, negative, missing-fact, exclusion/exemption, threshold, and
   multi-regime profiles. Activation requires 1.00 precision and 1.00 recall on approved cases.
8. API, UI, persistence, RLS, deletion, documentation, and Selenium tests pass; CI security gates
   remain green.

## Phase 9.0 — shared classification foundation

Outcome: support multiple reviewed regulatory classifications without weakening the current
HIPAA path.

- Add a reviewed source manifest schema with regime ID, classification, authority, version,
  effective date, source URL, and review metadata.
- Add an explicit `unknown`/`needs_review` result for missing or ambiguous scope facts. Absence of
  a fact must never silently mean “not applicable.”
- Preserve legal determinations as immutable records. Keep assurance objectives separate.
- Add regime classification to API and UI labels so regulation, SRO rule, audit objective, and
  contractual standard cannot be presented interchangeably.
- Promote candidate evals only through a dedicated ruleset review pull request.

Runnable gate: existing HIPAA evaluations remain unchanged; new classification and unknown-state
tests pass; no candidate fintech rule is active yet.

## Phase 9.1 — GLBA Safeguards Rule

Progress: **source review, detailed intake facts, and candidate boundary tests implemented**.
Protected ruleset activation and requirement-level ingestion/mapping remain pending human review.

Primary authority: [FTC Safeguards Rule guidance](https://www.ftc.gov/business-guidance/resources/ftc-safeguards-rule-what-your-business-needs-know).

- Replace the broad institution checkbox with reviewed FTC-jurisdiction, financial-activity,
  customer-information, and applicable exemption/supervision facts.
- Activate a versioned GLBA scope rule only after the reviewer signs off on those boundaries.
- Import a reviewed GLBA requirement artifact, including stable citations and effective dates.
- Load only publisher- or SCF-sourced mappings to installed controls.
- Add coverage, gaps, risk suggestions, policy types, export citations, and Audit Hub evidence.
- Expand the golden set with jurisdiction, non-customer information, exemption, and mixed-data
  negatives—not only the existing two-boolean happy path.

Runnable gate: an approved positive produces a GLBA determination and required-control set;
every approved negative/exempt/unknown profile produces the expected distinct result.

## Phase 9.2 — PCI DSS 4.0.1

Progress: **detailed assurance intake and source review implemented**. Installed identifier/mapping
validation and scope-driven workflow integration remain pending.

Primary authority: [PCI SSC document library](https://www.pcisecuritystandards.org/document_library/).

- Keep PCI DSS out of legal determinations. Collect merchant/service-provider role, account-data
  flow, environment scope, outsourcing, and validation-method facts.
- Suggest PCI readiness when account data is present, but require the user to confirm the
  contractual assurance objective.
- Validate the installed PCI identifiers and SCF mappings against the approved source version.
- Drive the full required-control, coverage, gap, risk, policy, export, and Audit Hub workflows.
- Test out-of-scope, outsourced-processing, merchant, service-provider, and unknown-scope cases.

Runnable gate: confirmed PCI scope creates a versioned assurance objective and traceable PCI
requirement set; the UI never says PCI DSS is a law or automatic legal determination.

## Phase 9.3 — US securities and New York finance

### Regulation S-P

Primary authority: [SEC final rule and amendments](https://www.sec.gov/rules-regulations/2024/06/s7-05-23).

- Capture the exact covered-institution category, size/compliance cohort, customer-information
  handling, and reviewed exclusions.
- Import reviewed requirement identifiers and effective/compliance dates, then source mappings.
- Add positive, category boundary, cohort, excluded, and unknown golden profiles.

### FINRA Rule 4370

Primary authority: [FINRA business-continuity guidance](https://www.finra.org/rules-guidance/key-topics/business-continuity-planning).

- Capture FINRA membership and the business/services needed for a tailored continuity scope.
- Label the result as an SRO obligation and preserve the reviewed rule citation.
- Load the reviewed requirement set and sourced mappings; do not infer cybersecurity obligations
  from adjacent guidance.

### 23 NYCRR Part 500

Primary authority: [NYDFS Cybersecurity Resource Center](https://www.dfs.ny.gov/industry_guidance/cybersecurity).

- Capture covered-license type, limited-exemption facts, Class A status, affiliate treatment, and
  transition dates required by the reviewed rule version.
- Model exemptions as explicit outcomes that retain their supporting facts and citations.
- Import reviewed Part 500 requirement identifiers and sourced mappings.

Runnable gate: all three regimes pass their approved boundary suites and independently drive
coverage without collapsing SEC, FINRA, and NYDFS into one generic finance label.

## Phase 9.4 — CCPA/CPRA

Primary authority: [California Privacy Protection Agency FAQ](https://cppa.ca.gov/faq).

- Replace the precomputed covered-business checkbox with reviewed threshold year/value facts,
  California consumer-data processing, related-entity treatment, and relevant exemptions.
- Version thresholds by effective period; never hardcode a “current” threshold without a date.
- Import reviewed statutory/regulatory requirement identifiers and sourced mappings.
- Add threshold-edge, exemption, related-entity, non-California, and unknown-data cases.

Runnable gate: profiles on either side of every approved threshold and exemption boundary produce
the reviewed result and retain the evaluated period.

## Phase 9.5 — DORA

Primary authority: [Regulation (EU) 2022/2554](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022R2554).

- Capture the Article 2 entity category, exclusions, group context, and whether the organization
  is a financial entity or an ICT third-party provider.
- Import article identifiers and official machine-readable text/provenance from EUR-Lex.
- Keep entity-level obligations separate from critical-provider oversight treatment.
- Add category, exclusion, provider, non-EU, and unknown profiles plus sourced control mappings.

Runnable gate: approved Article 2 cases create correctly labeled DORA determinations and scoped
requirements, with no model-generated legal interpretation.

## Phase 9.6 — Singapore MAS TRM Notices

Primary authority: [MAS Notice on Technology Risk Management FAQ](https://www.mas.gov.sg/-/media/mas-media-library/regulation/faqs/trpd/faqs---notice-on-technology-risk-management/faqs---notice-on-trm/faq---notice-on-technology-risk-management.pdf).

- Replace `mas_trm_notice_subject` with institution category, licence/status, and exact applicable
  notice number. One generic MAS boolean cannot activate obligation-level logic.
- Create one versioned source record per applicable notice; preserve its issue/effective dates.
- Ingest reviewed notice requirement identifiers and text only where licensing permits, then load
  publisher- or SCF-sourced mappings.
- Add a Singapore reviewer gate for institution categories, notice selection, exceptions, and
  transition provisions.

Runnable gate: the exact reviewed notice—not a generic “MAS TRM” label—drives the requirement set,
and unsupported institution types remain `needs_review`.

## Phase 9.7 — SOX Section 404

Primary authority: [SEC Section 404 rule](https://www.sec.gov/rules-regulations/2003/03/managements-report-internal-control-over-financial-reporting-certification-disclosure-exchange-act).

- Keep SOX as an ICFR reporting/audit objective. Capture Exchange Act reporting status, filer
  category, attestation status, reporting period, and reviewed exemptions.
- Model IT general controls as support for ICFR rather than claiming that SOX itself supplies a
  cybersecurity control catalog.
- Load reviewed objective identifiers, audit evidence expectations, and sourced mappings.
- Add filer-category, attestation, exemption, private-company, and unknown profiles.

Runnable gate: SOX scope creates the correct ICFR objective and evidence plan without appearing
as an automatically applicable cybersecurity law.

## Phase 9.8 — end-to-end release gate

- Merge the approved regime golden sets into the active evaluation harness and publish per-regime
  precision/recall plus the combined score.
- Add API integration tests proving determinations/objectives persist with facts and versions.
- Add one Selenium profile per classification track and verify coverage, policies, and Audit Hub.
- Run migrations, all backend tests, KB integrity validation, Ruff, frontend lint/type/build,
  dependency audits, Bandit, Semgrep, and Gitleaks.
- Update README status only after the corresponding production import and browser test pass.

Release criterion: no README card says “implemented” unless its active rule/objective, sourced
requirements, mappings, workflow, evaluation set, and production verification all pass.
