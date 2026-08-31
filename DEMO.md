# Ruleset 90-second demo

## Setup

Keep Docker, Ollama, FastAPI, and Next.js running. Use the seeded Northstar Health demo for
the public flow and a Clerk organization for live tenant actions.

## Walkthrough

**0–15 seconds — The problem**

Open the coverage matrix. Explain that Ruleset maps company facts and policy evidence to
compliance controls without trusting the language model to decide applicability.

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
rules, mappings come from OSCAL/SCF, tenant isolation comes from PostgreSQL RLS, and AI output
always requires human review.
