# Reviewer walkthrough captures

These images were captured from the deployed application by the authenticated Selenium walkthrough on 1 September 2026. The run used only the fictional LedgerPeak Payments tenant and passed all public-route, engagement-creation, and Audit Hub checks.

| Order | File | Stage to show |
| --- | --- | --- |
| 1 | `01-overview.png` | Signed-in homepage, organization switcher, intake, and coverage summary |
| 2 | `02-intake.png` | Company facts, regulatory inputs, and assurance objectives |
| 3 | `03-coverage.png` | Control matrix with an evidence quote and remediation gap selected |
| 4 | `04-risks.png` | Risk heatmap and tenant risk records |
| 5 | `05-monitoring.png` | GitHub/AWS connection controls and immutable evidence history |
| 6 | `06-questionnaires.png` | Grounded answer awaiting human approval |
| 7 | `07-framework-drift.png` | Framework comparison and affected policy statements |
| 8 | `08-policies.png` | Generated policy library and verified DOCX export action |
| 9 | `09-trust-center.png` | Implemented safeguards and evidence claims |
| 10 | `10-audit-share.png` | Expiring read-only Audit Hub evidence view |

Do not include credentials, tokens, browser profiles, real company data, or unrelated desktop applications in captures. Use only the fictional demonstration tenant.

Reproduce the public smoke test with `python -m uv run python scripts/selenium_portfolio.py --headless` from `apps/api`, or add `--capture` for the authenticated ten-stage walkthrough.
