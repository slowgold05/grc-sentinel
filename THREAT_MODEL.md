# GRC Sentinel Threat Model

## Assets

Customer documents, company profiles, generated policies, decision evidence, connector credentials, provider/API keys, and control knowledge-base integrity.

## Threats and controls

| Threat actor or event | Primary risk | Required controls |
|---|---|---|
| Curious or compromised tenant | Cross-organization disclosure | Non-superuser app role, forced PostgreSQL RLS, same-tenant foreign keys, permanent isolation test |
| Malicious uploaded document | Parser exploitation or prompt injection | Magic-byte and size validation, isolated parser worker, delimited untrusted prompt blocks, evidence substring checks |
| Hostile company domain or redirect | SSRF into private networks or cloud metadata | DNS resolution before requests, private/link-local denylist, scheme allowlist, redirect revalidation, response cap |
| Compromised dependency | Code execution or data theft | Pinned lockfiles, dependency audits, Bandit, Semgrep, Gitleaks, reviewed updates |
| LLM output | Fabricated citations, stored XSS, excessive spend | Pydantic schemas, deterministic citation verification, text-only rendering, length caps, concurrency and token budgets |
| Credential exposure | Account or provider compromise | Configuration-only secret loading, managed secret stores, log redaction, read-only connector scopes, rotation |
| Accidental retention | PDPA/GDPR erasure failure | Hard-delete cascade, expiry timestamps, daily sweeper, deletion tests |
| Knowledge-base corruption | Incorrect compliance claims | Official versioned sources, foreign keys, integrity gate, reviewed ruleset changes |

## Trust boundaries

Browser input, uploads, OSINT responses, connector responses, and LLM output are untrusted. The API validates each boundary. PostgreSQL—not application filters—is the final tenant-isolation boundary. The LLM never decides regulatory applicability and never authorizes a citation.

