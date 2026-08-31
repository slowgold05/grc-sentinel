# GRC Sentinel

GRC Sentinel is an AI-assisted governance, risk, and compliance (GRC) platform prototype. It turns a company profile and its existing policy evidence into an auditable compliance workspace: applicable requirements, control coverage, evidence gaps, risks, draft policies, monitoring results, and auditor-ready exports.

The key design decision is that the language model never decides what legally applies and is never trusted to invent evidence. Deterministic rules establish applicability, retrieval limits the model's context, and verification rejects unsupported citations before output can be stored.

> Portfolio prototype—not legal advice, a certification, or an audit opinion. Generated compliance material requires qualified human review.

**[Open the live recruiter demo](https://web-slowgold05s-projects.vercel.app)** · **[Check API health](https://api-production-3fd2d.up.railway.app/health)** · **[Read the 90-second demo script](DEMO.md)**

## What a reviewer can see

The public homepage contains a fictional healthcare engagement and an interactive control-coverage matrix. Select a control to inspect its exact policy evidence and remediation gap. The navigation demonstrates the risk register, continuous monitoring, questionnaire review, framework drift, policy library, and trust center.

The complete local build adds private document processing and local AI through Ollama. This split keeps the public portfolio inexpensive and prevents real policy text from being sent to a hosted model.

Current walkthrough captures are tracked in [`screenshots/`](screenshots/README.md). The previous homepage image is retained there until the refreshed black-and-red sequence is captured from the deployed application.

| Capability | What GRC Sentinel does | Why it matters |
| --- | --- | --- |
| Company intake | Captures industry, geography, data types, company facts, and contractual assurance goals | Gives every decision a reproducible facts snapshot |
| Applicability | Evaluates declarative rules for regulations such as HIPAA | Keeps legal applicability deterministic and testable |
| Assurance planning | Tracks SOC 2, ISO 27001, and NIST alignment separately from mandatory regulations | Avoids falsely presenting voluntary frameworks as laws |
| Control knowledge base | Ingests versioned NIST OSCAL and Secure Controls Framework records | Provides traceable control identifiers and mappings |
| Secure evidence upload | Validates, encrypts, parses, retains, and hard-deletes PDF/DOCX policies | Treats customer documents as hostile and sensitive input |
| RAG coverage analysis | Retrieves relevant policy sections and maps exact quotes to controls | Makes every coverage claim inspectable |
| Gap analysis | Classifies controls as covered, partial, or missing and recommends next steps | Turns policy evidence into an actionable remediation plan |
| Policy generation | Produces grounded drafts with control citations and DOCX traceability appendices | Speeds drafting without hiding the source controls |
| Questionnaire review | Generates evidence-backed answers that must be approved, edited, or rejected | Keeps a human in the decision loop |
| Risk register | Stores likelihood, impact, treatment state, and mapped controls in a heatmap | Connects compliance gaps to operational risk |
| Continuous monitoring | Runs read-only GitHub and AWS checks and stores immutable results | Detects when implemented safeguards drift from policy claims |
| Framework drift | Compares framework versions and identifies affected policy statements | Shows what must be reviewed when standards change |
| Audit Hub | Creates expiring read-only evidence shares and records access events | Supports scoped auditor collaboration |
| Trust center | Publishes implemented and planned safeguards with evidence | Demonstrates that the platform follows its own advice |
| Multi-tenancy | Maps Clerk organizations to internal tenant UUIDs protected by PostgreSQL RLS | Makes database isolation the final security boundary |

## End-to-end workflow

1. A user signs in through Clerk and creates or selects an organization.
2. GRC Sentinel provisions a tenant and stores only the resolved internal tenant UUID in database context.
3. The user describes the company and selects contractual or voluntary assurance objectives.
4. The deterministic rules engine evaluates which regulations apply and records the facts used.
5. The user uploads existing PDF or DOCX policies; GRC Sentinel validates, encrypts, and parses them into tenant-scoped sections.
6. Retrieval finds relevant policy sections for each required control.
7. Coverage analysis records exact supporting quotes and marks controls covered, partial, or missing.
8. The user reviews risks, remediation work, draft policies, and questionnaire answers.
9. Monitoring checks can create immutable evidence and flag pass-to-fail drift.
10. Approved material can be exported or shared through an expiring Audit Hub link.

## How the AI is constrained

GRC Sentinel uses retrieval-augmented generation (RAG), but deterministic software surrounds the model:

```mermaid
flowchart LR
    F[Company facts] --> R[Applicability rules]
    R --> C[Required controls]
    D[Encrypted policies] --> P[Hardened parser]
    P --> E[(Tenant evidence)]
    C --> Q[pgvector retrieval]
    E --> Q
    Q --> L[Local Ollama model]
    L --> V[Schema, citation, quote, and faithfulness checks]
    V --> H[Human review]
    H --> X[Stored result or DOCX export]
```

- Applicability is decided by declarative rules, not an LLM.
- Retrieved controls and policy sections bound the generation context.
- Pydantic schemas reject malformed output.
- Every generated control ID must exist in the retrieved context.
- Evidence quotes are checked against the source text.
- Unsupported or unfaithful output is rejected instead of silently stored.
- Generation has token budgets, retry limits, and concurrency controls.
- The default models run locally: `qwen3:14b` for generation and `mxbai-embed-large` for embeddings.

The reasoning behind this design is covered in [How GRC Sentinel rejects hallucinated citations](docs/hallucinated-citations.md).

## Architecture

```mermaid
flowchart TB
    U[Next.js 15 UI] -->|Clerk session token| A[FastAPI API]
    A --> R[Deterministic rules engine]
    A --> K[(PostgreSQL + pgvector + RLS)]
    A --> O[Passive OSINT]
    A --> M[Monitoring adapters]
    A --> G[Generation and verification]
    G --> L[Ollama / OpenAI-compatible endpoint]
    D[PDF and DOCX uploads] --> P[Constrained parser]
    P --> K
    K --> G
    G --> X[DOCX export]
```

| Layer | Technology | Responsibility |
| --- | --- | --- |
| Web | Next.js 15, React 19, Tailwind CSS | Responsive dashboard, Clerk UI, review workflows |
| API | FastAPI, Pydantic, SQLAlchemy | Validation, business rules, tenant APIs, generation orchestration |
| Data | PostgreSQL, pgvector, Alembic | Controls, evidence, vectors, audit history, RLS isolation |
| Identity | Clerk Organizations | Sign-in, organization membership, session verification |
| AI | Ollama with OpenAI-compatible APIs | Local generation and embeddings |
| Infrastructure | Docker Compose, Railway, Vercel | Reproducible local stack and public portfolio deployment |

## Framework and regulation coverage

The current knowledge base contains **6 framework records, 4,233 controls, 4,354 sourced crosswalk mappings, and 4,233 embeddings**.

- NIST SP 800-53 Rev. 5 controls come from official [NIST OSCAL content](https://github.com/usnistgov/oscal-content).
- Cross-framework identifiers come from the [Secure Controls Framework](https://securecontrolsframework.com/).
- HIPAA has executable applicability rules and a 30-profile evaluation set.
- SOC 2, ISO 27001, and NIST are modeled as contractual or voluntary assurance objectives.
- ISO standards text is not copied; the repository stores permitted identifiers and sourced mappings only.

The HIPAA golden set currently scores **1.00 precision and 1.00 recall**. The integrity check reports zero orphaned crosswalks. SCF does not currently provide a NIST path for SOC privacy criteria `P6.0` and `P6.4`; GRC Sentinel records those source-level gaps rather than inventing mappings.

## Security model

- Every tenant-owned row carries `org_id` and is protected by forced PostgreSQL row-level security.
- The runtime API uses a restricted database role; an owner connection is reserved for migrations.
- Clerk session tokens are verified server-side, including authorized-party checks.
- Clerk organization IDs are resolved to internal UUIDs before database access.
- Uploads are size- and magic-byte-validated, encrypted per tenant, and parsed with resource limits.
- URL fetching blocks private, loopback, link-local, and cloud-metadata destinations and revalidates redirects.
- Prompts clearly delimit user-controlled text and model output is length-capped and schema-validated.
- Audit evidence is append-only; audit-share links expire and can be revoked.
- Logs redact sensitive fields, and secrets remain in ignored local files or hosting secret stores.
- CI runs tests, migration checks, Bandit, Semgrep, Gitleaks, dependency audits, and frontend checks.

See [DATA_POLICY.md](DATA_POLICY.md), [THREAT_MODEL.md](THREAT_MODEL.md), and the live `/trust` page for the detailed boundaries.

## Tests and measurable checks

- 71 automated backend tests
- 30 HIPAA applicability evaluation profiles
- Property-based rules-engine tests
- Migration head checks
- Knowledge-base crosswalk integrity checks
- Frontend ESLint, TypeScript, and production-build validation
- Static analysis and secret/dependency scanning in CI

```powershell
Set-Location apps/api
python -m uv run pytest
python -m uv run ruff check .

Set-Location ../web
npm run lint
$env:VERCEL='1'; npm run build
```

## Run the full stack locally

Prerequisites: Docker Desktop, Python 3.12, Node.js 22+, `uv`, Corepack/pnpm, and Ollama.

```powershell
Copy-Item .env.example .env
```

Replace the example database passwords and generate a 32-byte base64 `UPLOAD_MASTER_KEY_BASE64`. Then install the local models and start the database:

```powershell
ollama pull qwen3:14b
ollama pull mxbai-embed-large
docker compose up -d
```

Prepare and start the API:

```powershell
Set-Location apps/api
python -m uv sync
python -m uv run alembic upgrade head
python -m uv run python -m ruleset.kb.embed_controls
python -m uv run uvicorn ruleset.main:app --reload
```

Start the web app in another terminal:

```powershell
corepack enable
pnpm install --frozen-lockfile
pnpm dev:web
```

Open `http://localhost:3000`; API health is at `http://localhost:8000/health`.

### Authentication

The hosted demo already uses the linked Clerk development instance. For a new local setup:

```powershell
Set-Location apps/web
clerk auth login
clerk init --app app_3IfQoM1pXe4hwChImmzYNgNVqha
clerk enable orgs --app app_3IfQoM1pXe4hwChImmzYNgNVqha --instance dev --force-selection --auto-create --max-members 5 --yes
clerk doctor
```

Email authentication is sufficient. Google and GitHub are optional sign-in conveniences and require provider configuration for a production Clerk instance.

## Deployment

The portfolio deployment uses:

- **Vercel:** public Next.js interface
- **Railway:** FastAPI and PostgreSQL/pgvector
- **Clerk:** development authentication and Organizations
- **Local laptop:** Ollama inference for the private full-stack demonstration

The public homepage is seeded so reviewers can explore the product without uploading data. Authenticated tenant workflows use the hosted API, while local Ollama-dependent generation remains a local demonstration to avoid GPU hosting cost and third-party policy disclosure.

See [DEPLOYMENT.md](DEPLOYMENT.md) for configuration, migration, and smoke-test details. Production Dockerfiles are included for both applications.

## Repository map

```text
apps/api/                 FastAPI source, migrations, ingestion, and tests
apps/web/                 Next.js dashboard and Clerk-authenticated workflows
docker/                   Least-privilege local PostgreSQL initialization
docs/                     Technical design notes
packages/shared-types/    OpenAPI-derived contract destination
screenshots/              Reviewer walkthrough images
```

The implementation plan is documented in [grc-platform-build-roadmap.md](grc-platform-build-roadmap.md). `PROJECT.md` records repository conventions and rebuilt state.

## Current limitations

- This is a portfolio prototype, not a compliance determination service.
- Executable applicability rules currently cover HIPAA; additional regulations require sourced rules and evaluation sets.
- The public deployment does not host Ollama. Run locally for private generation and embeddings.
- GitHub and AWS monitoring require explicitly scoped, read-only credentials.
- Have I Been Pwned domain exposure is omitted because it requires a verified-domain API account.
- Human approval remains mandatory for generated policies and questionnaire answers.
