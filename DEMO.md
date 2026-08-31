# GRC Sentinel 90-second demo

## Setup

Keep Docker, Ollama, FastAPI, and Next.js running. Use the seeded LedgerPeak Payments fintech
demo for the public flow and a Clerk organization for live tenant actions.

## Walkthrough

**0–15 seconds — The problem**

Open the coverage matrix. Explain that GRC Sentinel maps company facts and policy evidence to
PCI DSS 4.0.1 and SOC 2 controls without trusting the language model to establish obligations
or decide applicability.

**15–35 seconds — Evidence-backed gap analysis**

Select a covered, partial, and missing control. Show that every accepted coverage claim includes
an exact quote from the uploaded policy; unsupported model claims are rejected in code.

**35–55 seconds — Local AI with bounded authority**

Explain that local Ollama embeds the 4,233-control knowledge base and drafts structured policy
statements. Retrieval limits the allowed control IDs, and deterministic verification blocks
fabricated citations before storage.

**55–75 seconds — GRC beyond policy generation**

Open monitoring and the risk register. Show read-only GitHub/AWS checks, immutable evidence,
drift detection, and risks linked back to controls.

**75–90 seconds — Trust and auditability**

Open the trust page or an expiring Audit Hub link. Close with: applicability comes from versioned
rules, the displayed PCI DSS and SOC 2 crosswalks come from SCF, tenant isolation comes from
PostgreSQL RLS, and AI output always requires human review.
