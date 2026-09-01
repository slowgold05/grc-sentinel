# Two-minute portfolio video guide

Record at 1440p with browser zoom at 90–100%. Use only the fictional LedgerPeak Payments tenant.
Keep credentials, tokens, terminals containing secrets, and unrelated applications off screen.

## Recording checklist

1. Start Docker, the API, web app, and Ollama if demonstrating local generation.
2. Sign in and select the fictional Clerk organization before recording.
3. Close notifications and unrelated tabs.
4. Confirm the public smoke test passes:
   `python -m uv run python apps/api/scripts/selenium_portfolio.py --headless`.
   Use the refreshed [screenshots](../screenshots/README.md) as the expected visual sequence.
5. Record the walkthrough below in one take; trim only the beginning and end.
6. Export an MP4 at 1080p or 1440p, H.264, 30 fps, under three minutes.
7. Upload the video to an unlisted YouTube or portfolio-hosted page and add its link to README.
   Do not commit a large video binary to Git.

## Script and screen direction

| Time | Screen | What to say |
| --- | --- | --- |
| 0:00–0:15 | Homepage and fintech perimeter | “GRC Sentinel is an AI-assisted compliance workspace for fintechs. It separates regulations, SRO rules, reporting objectives, and contractual standards instead of treating them as interchangeable.” |
| 0:15–0:35 | Detailed intake | “The platform records entity, threshold, exemption, licence, and operational facts. Approved deterministic rules return applicable, not applicable, or needs review. The model never decides legal scope.” |
| 0:35–0:58 | Coverage matrix | “Uploaded policies are validated, encrypted, and retrieved against source-backed controls. Every accepted coverage result includes an exact evidence quote; missing controls produce a remediation gap.” |
| 0:58–1:20 | Architecture diagram | “NIST controls come from OSCAL and mappings come from SCF. Ollama drafts from a bounded retrieval context. Code rejects unsupported control IDs and evidence before anything is stored.” |
| 1:20–1:38 | Risks and monitoring | “Gaps become risks linked to controls. Read-only GitHub and AWS checks create immutable evidence and flag pass-to-fail drift.” |
| 1:38–1:53 | Policies or questionnaires | “Generated policies and questionnaire answers remain structured, cited, and subject to human approval.” |
| 1:53–2:08 | Audit Hub or trust center | “Auditors can receive an expiring read-only evidence share. Tenant isolation is enforced by PostgreSQL row-level security, and CI tests the same security controls the platform recommends.” |
| 2:08–2:15 | Homepage | “The key idea is not that AI writes compliance text—it is that every important AI output is constrained, traceable, and reviewable.” |

## After recording

- Verify names, email addresses, organization IDs, and tokens are not visible.
- Add captions; interviewers often watch without sound.
- Use the title: **GRC Sentinel — Verifiable AI Compliance for Fintech**.
- Suggested description: “A two-minute walkthrough of deterministic applicability, source-backed
  controls, local RAG, evidence verification, tenant isolation, monitoring, and audit sharing.”
- Architecture reference: [portfolio-architecture.svg](portfolio-architecture.svg).
