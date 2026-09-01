# Fintech regime release readiness

Audit date: 2026-09-01

## Verified foundation

- Three-state classification contract: `applicable`, `not_applicable`, `needs_review`.
- Detailed intake and persisted fact snapshots for GLBA, PCI DSS, Regulation S-P, FINRA 4370,
  NYDFS Part 500, CCPA/CPRA, DORA, MAS TRM Notices, and SOX Section 404.
- Classification labels keep regulation, SRO rule, reporting/audit objective, and contractual
  assurance standard distinct.
- 95 backend tests pass; Ruff, KB validation, frontend lint/type/production build, authenticated
  Selenium walkthrough, Bandit, Semgrep, Python dependency audit, and pnpm audit pass.
- PostgreSQL is healthy and Alembic is at head `0022`.
- The current Vercel production deployment and Railway health endpoint return 200, and the
  detailed ten-stage reviewer screenshots were refreshed from the deployed application.
- GLBA has a 32-profile candidate set plus a test-only activation contract covering persistence,
  required controls, verified gap evidence, and Audit Hub sharing.

## Protected activation backlog

No item below may be activated from model recall or semantic similarity.

The machine-validated activation contract for all nine regimes is in
[`fintech-activation-manifest.json`](fintech-activation-manifest.json). It records classification,
source-review artifact, mandatory approvals, minimum evaluation size, and browser acceptance gate.

| Regime | Human approval required before activation |
| --- | --- |
| GLBA | Approve the 32 candidate profiles and proposed citations; approve effective rule version, requirement import, and sourced mappings |
| PCI DSS 4.0.1 | Contractual scope/validation interpretation, official/licensed requirement source, golden profiles, sourced mappings |
| Regulation S-P | Covered-institution and compliance-date review, rule citations, golden profiles, requirement import, sourced mappings |
| FINRA 4370 | Membership/BCP scope review, SRO citations, golden profiles, requirement import, sourced mappings |
| NYDFS Part 500 | Authorization, exemption, Class A, and transition review; golden profiles, requirement import, sourced mappings |
| CCPA/CPRA | Period-specific thresholds and information-level exemptions, golden profiles, requirement import, sourced mappings |
| DORA | Article 2 categories/exclusions/nexus and Article 31 provider treatment, golden profiles, EUR-Lex import, sourced mappings |
| MAS TRM | Institution-to-current-FSM-notice mapping, versions/transitions/exceptions, golden profiles, notice imports, sourced mappings |
| SOX 404 | Filer/transition/attestation review, ICFR evidence methodology, golden profiles, sourced ITGC mappings |

After approval, each regime needs a protected ruleset/objective data PR, immutable versioned source
records, real requirement/control data, per-track authenticated Selenium coverage, and published
per-regime plus combined evaluation metrics. The shared GLBA workflow contract already proves the
generic persistence-to-Audit-Hub plumbing with explicitly non-authoritative test fixtures. Until
approval, the README must say “detailed foundation” or “awaiting human review,” never “implemented.”

## Environment note

On this Windows host, the ordinary standalone Next.js build can encounter symlink permission
errors. The documented Vercel-mode build completes locally, and Linux GitHub Actions remains the
release packaging authority. Gitleaks is provided by CI because no local binary is installed.
