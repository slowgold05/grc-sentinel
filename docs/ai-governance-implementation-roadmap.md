# AI governance and policy implementation roadmap

Status: **planned — implement one bounded task at a time**
Source review date: **2026-09-11**

This roadmap adds an auditable AI-governance lifecycle to GRC Sentinel. An LLM may retrieve and
draft, but it may not classify legal obligations, set risk tolerance, approve deployment, or invent
evidence. The tasks are deliberately small enough for a cheaper coding model.

## Product outcome

An organization can inventory an AI system; deterministically triage risk and candidate legal
scope; complete a versioned impact assessment; attach tests and immutable evidence; require human
approval before deployment or material change; manage incidents and exceptions; generate grounded
AI policies; and share an auditor-ready record through Audit Hub.

The portfolio scenario is one fictional fintech use case: an internal customer-support RAG
assistant that drafts answers but cannot send messages or take external actions.

## Source hierarchy

| Source | Classification | Product use |
| --- | --- | --- |
| [NIST AI RMF 1.0](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10) | Voluntary framework | Govern, Map, Measure, Manage taxonomy |
| [NIST AI 600-1](https://doi.org/10.6028/NIST.AI.600-1) | Voluntary GenAI profile | GenAI risk and action catalog |
| [NIST AI RMF Playbook](https://airc.nist.gov/airmf-resources/playbook/) | Voluntary guidance | Suggested actions, never universal requirements |
| [ISO/IEC 42001:2023](https://www.iso.org/standard/42001) | Certifiable voluntary standard | Assurance objective; identifiers and licensed metadata only |
| [EU AI Act](https://eur-lex.europa.eu/eli/reg/2024/1689/oj) | Binding EU regulation | Review-gated legal and operator-role overlay |
| [EU implementation timeline](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai) | Official guidance | Versioned application dates and later guidance |
| [Singapore Model AI Governance Framework](https://www.pdpc.gov.sg/help-and-resources/2020/01/model-ai-governance-framework) | Voluntary guidance | Traditional-AI governance objective |
| [Singapore GenAI framework](https://www.imda.gov.sg/resources/press-releases-factsheets-and-speeches/factsheets/2024/gen-ai-and-digital-foss-ai-governance-playbook) | Voluntary guidance | GenAI governance objective |
| [Singapore Agentic AI framework](https://www.imda.gov.sg/resources/press-releases-factsheets-and-speeches/press-releases/2026/new-model-ai-governance-framework-for-agentic-ai) | Voluntary guidance | Later tool-using-agent extension |

Pin NIST imports to `NIST AI 100-1 (2023)` because NIST says AI RMF 1.0 is being revised; changes
flow through framework drift. Store EU application dates as versioned source data, not timeless UI
copy. MAS FEAT, Veritas, and later supervisory guidance remain source-review tasks until a current
MAS primary artifact is acquired and approved.

## Trust boundaries

- AI never decides legal applicability, final risk, exceptions, or approval.
- Framework alignment is not certification; guidance is not law.
- Do not copy licensed ISO text. Store permitted identifiers, edition, and source metadata.
- Persist only publisher-sourced control mappings; similarity is not a mapping.
- Human reviewers set use-case-specific thresholds. Never invent universal fairness or safety bars.
- Treat prompts, output, datasets, incidents, and uploads as hostile tenant data subject to RLS,
  encryption, redaction, retention, and deletion.
- Ollama may summarize retrieved records and draft policy; it is never an authority.

## Minimal data model

Use five tenant-owned tables rather than a generic workflow engine:

- `ai_systems`: owner, purpose, lifecycle, model/vendor, users, affected persons, data, geography,
  autonomy/tool access, oversight, deployment, and next-review facts.
- `ai_assessments`: immutable versioned intake snapshot, internal risk, candidate legal result,
  identified harms, mitigations, residual risk, reviewer, and source versions.
- `ai_evaluations`: append-only definition/version, dataset reference, approved thresholds, metrics,
  verdict, model/configuration version, evidence reference, and execution time.
- `ai_approvals`: append-only assessment/deployment/change/exception/retirement decisions with actor,
  role, rationale, conditions, expiry, and timestamp.
- `ai_incidents`: severity, impact, containment, owner, evidence, resolution, and a human-set
  `regulatory_review_required` flag.

Lifecycle states: `draft`, `in_review`, `approved`, `deployed`, `suspended`, `retired`. Every table
gets `org_id NOT NULL`, forced RLS, retention treatment, deletion coverage, authorization tests,
and audit events. Add migrations; never edit applied migrations.

## Delivery sequence

Each subtask is one model session and one commit.

### Phase 10.0 — sources and typed vocabulary

**10.0.1 Source reviews.** Add reviews under `docs/ai-governance-sources/` for NIST AI RMF,
NIST AI 600-1, ISO 42001, the EU AI Act, and Singapore frameworks. Record publisher, identifier,
version/date, classification, URL, licensing restriction, caveat, and review date.

Done: every claim has a primary source; legal and voluntary sources are distinct; no ISO text is
copied.

**10.0.2 Contracts.** Add typed lifecycle, operator-role, internal-risk, candidate-legal-status,
approval, evaluation, and incident enums/models. Follow `risk_register.py` and `intake/models.py`.

Done: Pydantic rejects unknown values, excessive text, invalid dates, and impossible combinations;
one valid and one invalid unit case pass.

### Phase 10.1 — AI system inventory

**10.1.1 Persistence.** Add `ai_systems` using a new migration and the risks/assurance-objectives
repository pattern. Extend RLS, audit events, retention, and deletion.

Done: create/list/get/state-change APIs pass; another organization cannot read or mutate records;
hard deletion is covered; user content never enters logs.

**10.1.2 UI.** Add an AI Systems navigation item, list, create form, detail view, and lifecycle
badge by reusing existing UI and API-client patterns.

Done: validation, keyboard access, and loading/empty/error states pass an authenticated browser
assertion.

### Phase 10.2 — deterministic triage

**10.2.1 Internal risk.** Evaluate explicit facts—decision consequence, affected people, sensitive
data, external exposure, autonomy, tool permissions, and human oversight—from a reviewed versioned
JSON decision table. Return `low`, `medium`, `high`, `critical`, or `needs_review`, fired conditions,
and missing facts. This is internal prioritization, not law.

Done: pure deterministic evaluation, immutable facts, missing-fact property tests, and at least 30
reviewer-authored boundary profiles.

**10.2.2 EU AI Act candidate scope.** Capture geography, operator role, intended purpose,
prohibited-practice indicators, Annex III category, affected persons, GPAI role, and transparency
scenario. Return `candidate_prohibited`, `candidate_high_risk`, `candidate_transparency`,
`candidate_minimal`, `not_applicable`, or `needs_review`.

Done: keep the ruleset test-only until legal review approves articles/annexes, exclusions, operator
roles, dates, and at least 30 boundary profiles. UI must say “candidate assessment.”

**10.2.3 Objectives.** Let users select NIST AI RMF, ISO 42001, and Singapore alignment as
assurance objectives with basis, scope, target date, source version, and selector.

Done: UI and stored records label each objective voluntary or certifiable as appropriate and never
auto-apply it as law.

### Phase 10.3 — impact assessment and risks

**10.3.1 Assessment.** Add structured fields for purpose/limitations, stakeholders, benefits and
harms, data provenance, privacy, contextual fairness, explainability, security, robustness, human
oversight, vendor reliance, misuse, incident response, monitoring, and decommissioning.

Done: editable draft; submission creates an immutable version; missing material facts yield
`needs_review`; author, reviewer, and source versions are shown.

**10.3.2 Risk integration.** Add optional `ai_system_id` to the existing risk register instead of
building another risk engine.

Done: AI risks appear in the existing heatmap with ownership, treatment, controls, RLS, retention,
and deletion behavior tested.

### Phase 10.4 — human approval gates

**10.4.1 Append-only decisions.** Add assessment, deployment, material-change, exception, and
retirement approval records. Later decisions supersede but do not overwrite earlier ones.

Done: ordinary application paths cannot update/delete decisions; authorization is enforced; the
complete history remains visible.

**10.4.2 Deployment gate.** A pure service lists blockers when the current assessment, residual-risk
decision, required evaluation, unexpired exception, or legal-review gate is missing or failed.

Done: table-driven tests cover every blocker and all-clear; stale concurrent approvals fail; the
model can summarize blockers but cannot modify them.

### Phase 10.5 — evaluation evidence and drift

**10.5.1 Registry.** Support task performance, robustness, prompt injection, privacy leakage,
groundedness, harmful output, contextual fairness, oversight effectiveness, and reliability.
Definitions include dataset/version, population/context, metric direction, approved threshold,
owner, cadence, and limitations.

Done: unmeasured risks stay visible; thresholds require human approval; runs are append-only and
bound to exact model/configuration versions.

**10.5.2 Dogfood GRC Sentinel.** Use fictional fixed fixtures to test schema validity, citation and
quote fidelity, unsupported-control rejection, tenant separation, prompt-injection resistance,
refusal behavior, and token/cost limits.

Done: reproducible machine-readable report, zero unsupported stored citations, and CI regression
failure. Do not claim broad safety from the narrow dataset.

**10.5.3 Drift.** Reuse immutable evidence/drift patterns. Trigger review for material model,
prompt, corpus, tool-permission, purpose, vendor-term, or measured-performance changes.

Done: new versions create new evidence and invalidate only approvals whose recorded scope requires
it; old evidence remains visible.

### Phase 10.6 — AI policy suite

Generate separate drafts for AI governance/accountability, acceptable use, inventory/lifecycle,
risk and impact assessment, data/privacy, model validation and monitoring, third-party/foundation
models, human oversight/transparency/contestability, AI security/incidents, and generative/agentic
AI use.

Reuse retrieve → generate → verify → human review. Every statement may cite only retrieved
requirements/controls and link to evidence where available. Selected objectives determine the
corpus; the model cannot merge voluntary guidance with binding law silently.

Done: malformed output and unsupported citations are rejected; drafts are labeled; approval is
human-only; DOCX includes source versions, traceability, approver, and gaps.

### Phase 10.7 — incidents, exceptions, and vendors

**10.7.1 Incidents.** Add create/triage/contain/resolve states with immutable audit history and links
to systems, risks, evaluations, and evidence. Reportability always goes to human/legal review.

**10.7.2 Exceptions.** Reuse approval records for time-limited accepted risk with owner, reason,
compensating controls, expiry, and review. Expired exceptions block deployment.

**10.7.3 Vendors.** Initially keep provider, model, hosting region, data-use terms, subprocessors,
security artifacts, contract date, and review date in the AI system. Normalize vendors only when
multiple systems need a genuinely shared vendor lifecycle. Missing facts become review gaps; no
crawler or model asserts contract terms.

### Phase 10.8 — dashboard and Audit Hub

Show inventory, risk distribution, overdue reviews, blockers, failed evaluations, incidents, and
expiring exceptions. Extend Audit Hub with a scoped system record containing assessment version,
objectives, risks, evaluations, approvals, policies, evidence, incidents, and exclusions.

Done: share is read-only, expiring, revocable, access-logged, and restricted to one tenant/system;
the public demo uses fictional data only.

### Phase 10.9 — release gate

Before claiming implementation:

1. one migration head exists and downgrade is tested;
2. RLS/authorization covers every table and route;
3. retention, deletion, redaction, and append-only history tests pass;
4. imports validate identifiers, provenance, versions, and licensing;
5. each activated legal classifier has at least 30 approved boundary profiles;
6. published evaluation metrics include dataset scope and limitations;
7. backend tests, Ruff, KB validation, frontend lint/type/build, dependency audits, Bandit,
   Semgrep, and Gitleaks pass; and
8. authenticated Selenium proves inventory → assessment → risk → evaluation → approval → policy →
   Audit Hub.

## Cheap-model execution protocol

Give the coding model one subtask, never this whole roadmap:

```text
Read PROJECT.md, CONVENTIONS.md, AGENTS.md, and roadmap task <ID> completely.
Implement only <ID>.
Outcome: <copy outcome>. Allowed files: <exact list>.
Pattern references: <one or two existing files>.
Do not add dependencies, edit applied migrations/generated types/protected rulesets, invent legal
rules or thresholds, copy ISO text, infer mappings, or let AI make applicability/approval decisions.
Trace the existing flow, state the smallest runnable definition of done, implement it, run the
narrow test, then required repo checks. If a source or interface is missing, report that exact
blocker without expanding scope.
```

Require this handoff:

```text
Changed files:
Tests and exact results:
Security/tenancy/retention impact:
Source and version:
Known limitations:
Next task (do not implement):
```

Reject changes outside the task, one-use abstractions, invented mappings/thresholds, missing
RLS/deletion tests, or test claims without output.

## Recommended portfolio cut

Complete phases 10.0–10.6, one fictional RAG-assistant evaluation pack, and the 10.8 Audit Hub
view. Vendor normalization and agentic execution controls can wait until multiple vendors or
tool-using agents exist.

Interview story: **“I built a governed AI lifecycle where deterministic rules triage risk and
candidate legal scope, immutable evidence proves evaluations, humans control deployment, and the
model can draft policy but cannot approve itself.”**
