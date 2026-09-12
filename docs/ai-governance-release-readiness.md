# AI governance release readiness

## Implemented portfolio scope

GRC Sentinel now covers a governed lifecycle for a fictional fintech support assistant:

- tenant-isolated inventory and lifecycle states;
- deterministic internal-risk triage and review-gated EU AI Act candidate scope;
- immutable impact-assessment, model/configuration, evaluation, and decision versions;
- nine evaluation categories with human-approved thresholds and drift detection;
- a human-controlled deployment gate;
- ten separate policy draft types grounded only in selected, installed objectives;
- append-only incidents, time-limited exceptions, and vendor review gaps; and
- dashboard metrics plus expiring, revocable, system-scoped Audit Hub records.

The model cannot decide applicability, set thresholds, approve assessments or policies, decide
incident reportability, or authorize deployment.

## Source and generation status

The local database imports 72 NIST AI RMF 1.0 outcomes from NIST's official Playbook JSON and
embeds all 72 with `mxbai-embed-large`. Optional Playbook actions remain labelled voluntary
suggestions. ISO/IEC 42001 content is not copied, and Singapore content is not activated without an
approved publisher corpus.

The live local `qwen3:14b` smoke test completed retrieve → generate → deterministic citation
verification → independent faithfulness verification → draft storage. Unsupported, malformed, or
unfaithful output fails before storage. Human approval is a separate append-only action.

## Verification evidence

- Alembic has one head through migration `0034`; new migrations downgrade and reapply.
- 138 backend tests pass, including tenancy, append-only history, stale-write protection, source
  selection, invalid citations, incident transitions, exception expiry, and audit sharing.
- Ruff, Python compilation, frontend ESLint, and TypeScript checks pass.
- Python and JavaScript dependency audits report no known vulnerabilities.
- Bandit reports no issues; Semgrep reports zero blocking findings.
- Zero imported NIST AI RMF outcomes lack embeddings.

On this Windows host, Next.js completes compilation, type validation, and static-page generation,
then cannot create standalone-output symlinks (`EPERM`). Linux CI is the packaging authority.
Gitleaks remains enforced by GitHub Actions because the executable is not installed locally.

## Claims not made

- This is a portfolio prototype, not legal advice, certification, an audit opinion, or a compliance
  determination service.
- NIST AI RMF alignment is voluntary and does not establish certification.
- The narrow fixed evaluation pack does not establish broad model safety.
- Candidate EU AI Act scope is not a legal conclusion.
- Incident notification/reportability requires qualified human and legal review.
- The hosted demo does not run Ollama; private generation remains local.
