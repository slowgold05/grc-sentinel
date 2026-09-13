# Reviewer walkthrough captures

Public UI captures were refreshed on 13 September 2026 for the screenshot-led Sentinal overhaul.
They contain only fictional, read-only examples. They do not prove authenticated submissions,
AI inference, legal approval, or a completed audit.

During local UI verification, Clerk emitted a session-refresh configuration warning. No
credentials were changed, and authenticated sign-in/submissions were not revalidated in this
pass. This warning is separate from the passing public-navigation and signed-out checks.

| File | Stage shown |
| --- | --- |
| `01-overview.png` | Public homepage: plain-language introduction and clearly labelled example |
| `04-risks.png` | Fictional risks with priorities, owners, and next actions; heatmap collapsed |
| `13-dark-theme.png` | Homepage in dark mode |
| `14-public-demo.png` | Public assessment excerpts, AI-system example, and illustrative policy |
| `15-mobile.png` | Narrow-screen navigation, account controls, and homepage |
| `16-navigation.png` | Expanded Platform menu with direct access to workspace tools |

The following captures are retained from earlier authenticated walkthroughs. Their visual design
may predate the current navigation; a new authenticated capture was not part of this UI pass.

| File | Historical stage |
| --- | --- |
| `02-intake.png` | Company facts, regulatory inputs, and assurance objectives |
| `03-coverage.png` | Evidence quote and remediation gap |
| `05-monitoring.png` | GitHub/AWS connection controls and evidence history |
| `06-questionnaires.png` | Answer review |
| `07-framework-drift.png` | Framework comparison |
| `08-policies.png` | Policy library and export |
| `09-trust-center.png` | Platform safeguards |
| `10-audit-share.png` | Engagement-scoped Audit Hub |
| `11-ai-systems.png` | AI inventory and lifecycle |
| `12-ai-audit-share.png` | System-scoped AI governance Audit Hub |

From `apps/api`, run:

```powershell
python -m uv run python scripts/selenium_ui_review.py --base-url https://web-six-xi-53.vercel.app
python -m uv run python scripts/selenium_portfolio.py --headless
python -m uv run python scripts/selenium_portfolio.py --capture
```

The UI review checks five viewport widths, hover/keyboard menus, product-image loading, account
controls, light/dark themes, hero-text contrast, theme persistence, reduced motion, public examples,
routes, and signed-out workspace
gating. It saves public images to `.tmp-ui-checks/` at the repository root by default.

The homepage uses three panel captures in `apps/web/public/product/`, taken from the public demo
in light mode. To refresh these illustrative images without accessing tenant records, run from
`apps/api` against the desired deployment (or pass a local `--base-url`):

```powershell
python -m uv run python scripts/selenium_ui_review.py --base-url https://web-six-xi-53.vercel.app --capture-assets ../web/public/product
```

These assets contain neither Drata's imagery nor authenticated Audit Hub records. The supplied
Drata recording was used only as a layout reference and is not included in the deployment.

The authenticated capture pauses for Clerk sign-in and organization selection in **Workspace**.
It creates fictional assessment and AI records and expiring audit shares. Its updated
`03-coverage.png` capture comes from the public illustrative assessment, not tenant analysis.
Refresh authenticated captures only with a fictional test organization.

Do not include credentials, tokens, browser profiles, real company data, or unrelated desktop
applications in captures.
