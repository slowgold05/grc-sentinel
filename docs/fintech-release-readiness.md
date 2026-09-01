# Fintech regime release readiness

Audit date: 2026-09-01

## Verified foundation

- Three-state classification contract: `applicable`, `not_applicable`, `needs_review`.
- Detailed intake and persisted fact snapshots for GLBA, PCI DSS, Regulation S-P, FINRA 4370,
  NYDFS Part 500, CCPA/CPRA, DORA, MAS TRM Notices, and SOX Section 404.
- Classification labels keep regulation, SRO rule, reporting/audit objective, and contractual
  assurance standard distinct.
- 92 backend tests pass; Ruff, KB validation, frontend lint/type compilation/static generation,
  Selenium public smoke, Bandit, Semgrep, Python dependency audit, and pnpm audit pass.
- PostgreSQL is healthy and Alembic is at head `0022`.

## Protected activation backlog

No item below may be activated from model recall or semantic similarity.

The machine-validated activation contract for all nine regimes is in
[`fintech-activation-manifest.json`](fintech-activation-manifest.json). It records classification,
source-review artifact, mandatory approvals, minimum evaluation size, and browser acceptance gate.

| Regime | Human approval required before activation |
| --- | --- |
| GLBA | FTC scope/exemptions, effective version, cited rules, 30+ golden profiles, requirement import, sourced mappings |
| PCI DSS 4.0.1 | Contractual scope/validation interpretation, official/licensed requirement source, golden profiles, sourced mappings |
| Regulation S-P | Covered-institution and compliance-date review, rule citations, golden profiles, requirement import, sourced mappings |
| FINRA 4370 | Membership/BCP scope review, SRO citations, golden profiles, requirement import, sourced mappings |
| NYDFS Part 500 | Authorization, exemption, Class A, and transition review; golden profiles, requirement import, sourced mappings |
| CCPA/CPRA | Period-specific thresholds and information-level exemptions, golden profiles, requirement import, sourced mappings |
| DORA | Article 2 categories/exclusions/nexus and Article 31 provider treatment, golden profiles, EUR-Lex import, sourced mappings |
| MAS TRM | Institution-to-current-FSM-notice mapping, versions/transitions/exceptions, golden profiles, notice imports, sourced mappings |
| SOX 404 | Filer/transition/attestation review, ICFR evidence methodology, golden profiles, sourced ITGC mappings |

After approval, each regime needs a new protected ruleset/objective data PR, immutable versioned
source records, API persistence tests, per-track authenticated Selenium coverage, and published
per-regime plus combined evaluation metrics. Until then, the README must say “detailed foundation”
or “awaiting human review,” never “implemented.”

## Environment note

On this Windows host, Next.js completes compilation, lint/type validation, page-data collection,
and static-page generation, then Windows denies the standalone output symlinks with `EPERM`.
The Linux GitHub Actions build remains the release packaging authority. Gitleaks is also provided
by CI because no local binary is installed.
