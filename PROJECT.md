# PROJECT.md — Ruleset (AI GRC Policy Platform)

> **Instructions to the AI assistant:** Read this entire file before writing any code.
> You implement exactly ONE task per session (see CURRENT TASK at the bottom).
> Do not modify any file outside the paths listed in the task. Do not invent
> interfaces — every type, schema, and function signature you need already
> exists in `packages/shared-types` or the task spec. If something you need
> is missing, STOP and say what's missing instead of guessing.

---

## 1. What this project is

Ruleset generates audit-ready information-security policies. A deterministic
rules engine decides which regulations (HIPAA, PCI DSS, SOC 2, GDPR, PDPA…)
apply to a company; a retrieval-bounded LLM pipeline drafts policies that cite
security controls (NIST 800-53, mapped via crosswalks to SOC 2 / ISO 27001 IDs);
a deterministic verifier rejects any output citing a control that was not in
the retrieval context.

**Core design rule: the LLM is the least-trusted component.** Applicability is
never decided by a model. Citations are never trusted without verification.
If a task ever seems to require the model to "just know" a control or
regulation, the task is wrong — flag it.

**Second design rule: this is a security product, built like one.** Untrusted
input includes uploads, OSINT responses, user-supplied strings, AND LLM output.
Tenant isolation is enforced by the database (RLS), not by application code.
The security conventions in section 6b are as binding as the type system.

---

## 2. Architecture

```
apps/web (Next.js) ──HTTP──▶ apps/api (FastAPI) ──▶ Postgres 16 + pgvector
        │                           │                (RLS on all tenant tables)
   auth provider ──sessions──▶ middleware sets app.org_id per request
                                    │
                                    ├─ rules engine   (pure functions, JSON rules)
                                    ├─ kb ingestion   (OSCAL, SCF → controls/crosswalks)
                                    ├─ osint modules  (passive-only, SSRF-guarded, cached)
                                    ├─ uploads        (validated, sandboxed parse, encrypted at rest)
                                    ├─ retention      (daily sweeper enforcing DATA_POLICY.md)
                                    ├─ monitoring     (ControlTest connectors: GitHub, AWS read-only →
                                    │                  immutable evidence records, drift alerts)
                                    ├─ questionnaires (answers grounded in statements table, verified)
                                    └─ genpipeline    (retrieve → generate → verify → assemble)
                                            │
                                            └──▶ Anthropic API (Sonnet = generate, Haiku = verify;
                                                 semaphore-capped, per-engagement token budget)
```

Generation pipeline stages (each a pure-ish function, each independently tested):

```
plan → retrieve → generate → verify_citations (deterministic) → verify_faithfulness (LLM) → assemble → export_docx
```

---

## 3. Repository map

```
/
├── PROJECT.md              ← this file
├── CONVENTIONS.md          ← code style, error handling, logging patterns
├── THREAT_MODEL.md         ← assets, actors, mitigations (STRIDE-lite)
├── DATA_POLICY.md          ← data classes, retention periods, deletion rules
├── apps/
│   ├── web/                ← Next.js 14 App Router, TypeScript strict, Tailwind
│   │   └── src/{app,components,lib}/
│   └── api/                ← FastAPI, Python 3.12, uv
│       └── src/ruleset/
│           ├── models/     ← Pydantic v2 models (mirror of shared-types)
│           ├── routers/    ← FastAPI routers, thin: validate → call service → respond
│           ├── services/   ← business logic, no FastAPI imports allowed here
│           ├── rules/      ← rules engine + rulesets/*.json (versioned)
│           ├── kb/         ← ingestion scripts + retrieval
│           ├── osint/      ← one module per source, all implement OsintCheck protocol
│           ├── genpipeline/← one file per pipeline stage
│           ├── security/   ← ssrf_guard.py, crypto.py (envelope encryption), redaction.py
│           ├── uploads/    ← validation, sandboxed parsing worker
│           ├── retention/  ← sweeper job, delete_engagement cascade
│           ├── monitoring/ ← ControlTest protocol, one connector per file (github.py, aws.py), scheduler
│           ├── questionnaires/ ← question extraction, statement retrieval, answer generation + verification
│           └── db/         ← SQLAlchemy models, alembic migrations, rls_policies.sql
├── packages/shared-types/  ← generated from OpenAPI; NEVER edit by hand
└── tests/                  ← mirrors src structure; pytest + hypothesis
```

---

## 4. Stack (pinned)

| Layer | Choice | Notes |
|---|---|---|
| Frontend | Next.js 14, TS `strict: true` | no `any`, no `@ts-ignore` |
| Backend | FastAPI + Pydantic v2 | Pydantic model on EVERY function boundary |
| DB | Postgres 16 + pgvector | one DB for relational + embeddings |
| Migrations | alembic | never edit an applied migration |
| Tests | pytest, hypothesis, vitest | tests define "done" |
| LLM | Anthropic API | model IDs live in `config.py`, never inline |
| Auth | managed provider (Clerk/Auth0/Supabase) | never hand-rolled |
| Tenancy | Postgres RLS, `org_id` on every tenant table | DB enforces isolation, not app code |
| Secrets | `.env` local / platform store deployed | loaded only via `config.py::settings` |
| CI security | gitleaks, pip-audit, pnpm audit, bandit, semgrep | gates block merge |
| Package mgmt | pnpm (web), uv (api) | lockfiles pinned |

---

## 5. Domain glossary (use these exact terms)

- **Control** — a single security requirement, e.g. NIST `AC-2`. Table: `controls`.
- **Crosswalk** — a mapping between two controls in different frameworks
  (`AC-2` ↔ `SOC2 CC6.2`). Table: `crosswalks`. Source of truth: SCF import.
- **Determination** — output of the rules engine: one applicable regulation +
  the rule that fired + input-facts snapshot. Immutable once written.
- **Engagement** — one company's end-to-end run (intake → policies).
- **Statement** — one numbered policy requirement, citing ≥1 control ID.
- **Retrieval context** — the exact set of controls handed to the generator.
  A statement may only cite IDs from this set. No exceptions.
- **ControlTest** — a read-only check against a connected system (GitHub, AWS),
  mapping to ≥1 control ID. Pure function over fetched state; versioned
  `test_id` like `github-org-mfa-v1`.
- **Evidence record** — an immutable row proving a ControlTest ran: raw API
  JSON, verdict, timestamp, test version, control IDs. Append-only — a
  correction is a NEW row, never an UPDATE or DELETE (except retention sweep).
- **Drift** — a control's ControlTest transitioning pass → fail between runs.
  Drift creates an alert and an audit_event.
- **Answer** — a questionnaire response citing ≥1 statement ID from this org's
  approved statements. Same verification rule as statements: cited IDs must
  exist in the retrieval set.

---

## 6. Non-negotiable conventions (full detail in CONVENTIONS.md)

1. **Pure core, thin shell.** Services and pipeline stages are pure functions
   over Pydantic models. I/O (DB, HTTP, LLM calls) happens only at the edges,
   behind interfaces defined in `services/ports.py`.
2. **No naked LLM output.** Every LLM call requests JSON matching a Pydantic
   schema; parse with `Model.model_validate_json`, retry once on failure, then
   raise `GenerationSchemaError`.
3. **Errors:** raise typed exceptions from `ruleset/errors.py`; routers map
   them to HTTP codes. Never `except Exception: pass`.
4. **Logging:** `structlog`, one event per pipeline stage, always include
   `engagement_id`. No print statements.
5. **OSINT is passive-only.** Public records and plain GETs to public pages.
   Any task asking for scanning/probing is out of scope — refuse it.
6. **ISO 27001:** store clause IDs only, never clause text (licensing).
7. **Determinism:** rules engine and citation verifier contain zero LLM calls
   and zero randomness. If a test needs `time.now()`, inject a clock.

---

## 6b. Security conventions (binding — violations fail review even if tests pass)

1. **Tenancy:** every new tenant-owned table gets `org_id uuid NOT NULL` and an
   RLS policy in `db/rls_policies.sql`. Queries never filter by `org_id`
   manually as the *only* isolation — RLS is the enforcement layer; app-level
   filters are convenience. Never write code that disables or bypasses RLS
   (`SET row_security = off`, superuser connections in app code).
2. **Secrets:** only `config.py` touches environment variables. Never hardcode
   keys, tokens, or URLs-with-credentials; never write a secret to a log,
   error message, or test fixture.
3. **Logging redaction:** never log document content, prompt bodies, LLM
   responses, or the `company` jsonb. Log IDs, event names, counts, durations.
   The structlog redaction processor in `security/redaction.py` is mandatory
   in every logger setup — copy the existing pattern.
4. **SQL:** SQLAlchemy expressions or bound parameters only. String-formatted
   SQL is forbidden (semgrep will flag it; don't fight the rule).
5. **Outbound HTTP:** all fetches go through `security/ssrf_guard.py::safe_fetch`
   (DNS-resolves first, refuses private/link-local/metadata ranges, http/https
   only, re-validates after redirects, size-capped). OSINT modules pass paths
   to pinned base URLs from config — never construct full URLs from user input.
6. **Uploads:** validate magic bytes + size cap before parsing; parsing runs in
   the sandboxed worker (`uploads/parse_worker.py`), never in the request
   handler. Stored bytes go through `security/crypto.py` envelope encryption.
7. **Untrusted text in prompts:** any user-supplied or document-derived string
   interpolated into an LLM prompt must be wrapped with
   `wrap_untrusted(text, label)` from `genpipeline/prompt_utils.py`, which
   delimits it as data. Instructions and data never share a block.
8. **LLM output is untrusted:** schema-validate, length-cap, and store as text.
   The frontend renders statements as text nodes, never `dangerouslySetInnerHTML`.
9. **Deletion & retention:** any feature that stores new tenant data must
   (a) be added to `retention/delete_engagement.py`'s cascade and its test, and
   (b) get a row in DATA_POLICY.md with a retention period. No orphan data.
10. **Dependencies:** never add one (rule 8.5 below); never pin around a CVE
    that pip-audit flags — surface it instead.
11. **Monitoring connectors are read-only.** ControlTests only ever GET/describe
    — never create, modify, or delete anything in a connected system. Connector
    credentials must be minimal read-only scopes, stored per-org via
    `security/crypto.py` envelope encryption, and never logged. Connector
    endpoints are pinned in config (rule 5 applies — no user-constructed URLs).
    A task asking a connector to remediate or write is out of scope — flag it.
12. **Evidence records are append-only.** No UPDATE or DELETE statements against
    the `evidence` table anywhere in app code; corrections are new rows. The
    only deletion path is the retention sweeper / engagement cascade.
13. **Questionnaire answers follow the citation rule.** Answers may only cite
    statement IDs present in their retrieval set, enforced by the same
    deterministic verifier pattern as `verify_citations`. Questionnaire file
    content is untrusted (rules 6 and 7 apply in full).

---

## 7. Data model summary (full DDL in `db/schema.sql`)

```
-- shared reference data (no org_id, no RLS)
frameworks(id, name, version, publisher, source_url)
controls(id, framework_id, control_code, title, description, params jsonb, valid_from, valid_to)
crosswalks(control_a, control_b, relation, strength, source)
regulations(id, name, jurisdiction, citation)
control_embeddings(control_id, embedding vector(1024), chunk_text)

-- tenant data (org_id + RLS on EVERY table below)
orgs(id, name, created_at)
users(id, org_id, auth_provider_id, role)            -- role: 'owner'|'member'
engagements(id, org_id, company jsonb, created_at, expires_at)
uploads(id, org_id, engagement_id, filename, sha256, enc_blob_ref, created_at)
upload_chunks(id, org_id, upload_id, seq, text, embedding vector(1024))
determinations(id, org_id, engagement_id, regulation_id, rule_id, rule_version, facts jsonb, created_at)
policies(id, org_id, engagement_id, policy_type, status)
statements(id, org_id, policy_id, seq, text, control_ids text[], verified bool)
osint_cache(id, org_id, domain, check_name, result jsonb, fetched_at, expires_at)
connections(id, org_id, provider, enc_credentials_ref, scopes, status, created_at)   -- provider: 'github'|'aws'
control_tests(id, org_id, connection_id, test_id, test_version, control_ids text[], schedule, enabled)
evidence(id, org_id, connection_id, test_id, test_version, control_ids text[], verdict, raw_response jsonb, tested_at)  -- APPEND-ONLY
questionnaires(id, org_id, engagement_id, upload_id, status, created_at)
questions(id, org_id, questionnaire_id, seq, text)
answers(id, org_id, question_id, text, statement_ids uuid[], verified bool, review_status)  -- 'proposed'|'approved'|'rejected'
risks(id, org_id, title, description, likelihood int, impact int, score int, status, treatment, control_ids text[], created_at)
share_links(id, org_id, engagement_id, token_hash, expires_at, created_at)
llm_calls(id, org_id, engagement_id, stage, model, input_tokens, output_tokens, cost_usd, created_at)
audit_events(id, org_id, engagement_id, actor, event, detail jsonb, created_at)
```

Retention (authoritative table in DATA_POLICY.md): uploads + enc blobs 90d
default; osint_cache 30d; evidence 1y (it's audit proof); audit_events 1y;
share_links deleted at expiry; everything cascades on `delete_engagement`,
and `connections` + their credentials are hard-deleted when an org disconnects
a provider. The sweeper in `retention/` enforces `expires_at`.

---

## 8. How to work in this repo (rules for the AI assistant)

1. Implement only the CURRENT TASK. Touch only its listed paths.
2. Run the task's tests mentally against your code before presenting it.
3. Match existing patterns — open the named "pattern reference" file first
   and copy its structure.
4. Keep outputs under ~150 lines. If the task can't fit, say so; don't compress
   by skipping error handling.
5. Never add dependencies. If one seems needed, stop and ask.
6. Never modify: `packages/shared-types/`, applied migrations, `rulesets/*.json`
   (rule changes are human-reviewed PRs), `db/rls_policies.sql` (security-
   reviewed PRs only), `security/` modules (use them, don't edit them), this file.
7. Security conventions (section 6b) apply to every task even when the task
   spec doesn't mention them. If a task seems to require violating one —
   logging a document body, fetching a raw user URL, skipping RLS — STOP and
   flag the conflict instead of implementing it.
8. Definition of done: listed tests pass, typechecker passes, no new lint
   errors, no new semgrep/bandit findings, docstring on every public function,
   and — if the task stores new tenant data — the deletion cascade and
   DATA_POLICY.md rows are updated (or the task explicitly says a follow-up
   task covers it).

---

## 9. Rebuild status

The repository has been rebuilt through roadmap Part 7.5. Alembic head `0016`
includes the knowledge base, tenancy, uploads, coverage, OSINT, generated
policies, monitoring evidence, questionnaire answers, risks, audit shares, and
retention enforcement and Clerk organization authentication. The backend suite contains 62 passing tests; the web
app exposes the coverage demo, trust page, and risk heatmap.

Remaining external inputs are Clerk application keys, live provider credentials,
hosting, and portfolio publishing. Protected tenant APIs verify Clerk sessions and
map the active organization to an internal UUID before setting `app.org_id`.
