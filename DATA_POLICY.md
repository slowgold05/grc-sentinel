# GRC Sentinel Data Policy

GRC Sentinel minimizes stored customer data and hard-deletes it when its purpose expires. These periods are maximums; an organization may choose shorter retention.

| Data class | Examples | Protection | Retention |
|---|---|---|---|
| Tenant secrets | Session and connector tokens | Managed auth provider or envelope encryption; never logged | Session lifetime or immediate deletion on disconnect |
| Uploaded documents | Existing policies and questionnaires | Per-organization envelope encryption | 90 days by default; delete with engagement |
| Derived artifacts | Assurance objectives, AI impact-assessment drafts and versions, chunks, embeddings, gap results, generated policies | Database encryption and tenant RLS | Life of engagement |
| AI system inventory | Validated purpose, owner, model/vendor, data, geography, autonomy, oversight facts, and immutable configuration versions | Tenant RLS; lifecycle and material changes are audited | Life of engagement |
| Decision evidence | Facts snapshots, determinations, AI governance decisions, audit events | Tenant RLS; append-only where specified | 1 year |
| OSINT cache | Public DNS and web posture | Tenant RLS | 30 days |
| Control and AI evaluation evidence | Read-only connector responses, versioned AI evaluation definitions, approved thresholds, and immutable verdicts | Tenant RLS; append-only evidence | 1 year |
| Share links | Hashed access tokens | Tenant RLS; raw token never stored | Delete at expiry |

Engagement deletion is a hard-delete cascade covering uploads, encrypted blobs, chunks, determinations, policies, statements, questionnaires, answers, and generated artifacts. A daily sweeper enforces expiry. Backups follow the hosting provider's documented deletion window and are never restored selectively after an erasure request.

Logs contain identifiers, event names, counts, durations, and verdicts only. They never contain document text, company profiles, prompts, model responses, credentials, or access tokens.
