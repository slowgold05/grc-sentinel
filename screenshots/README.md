# Reviewer walkthrough captures

The public and signed-in captures were refreshed on **14 September 2026** from
[the deployed app](https://web-six-xi-53.vercel.app). They show the current Sentinel GRC interface:
horizontal navigation, light/dark themes, the evidence-trail homepage, progressive intake, and
labelled Audit Hub summaries. These are screenshots of the application, not design mockups.

All 17 walkthrough images now show the supplied Sentinel GRC branding. The original uploaded
logos are preserved; deployment copies live in `apps/web/public/brand/`. The compact mark is
shared by the header, homepage preview, and footer; the full logo appears on sign-in/sign-up
pages and in link-preview metadata.

## Screenshot index

| File | Stage shown | Data and session |
| --- | --- | --- |
| [frontpage.png](frontpage.png) | First-screen homepage preview used at the top of the README | Public, fictional example |
| [01-overview.png](01-overview.png) | Complete homepage in light mode | Public, fictional example |
| [02-intake.png](02-intake.png) | Regulatory review with one expanded panel and assurance objectives | Signed in, fictional company facts |
| [03-coverage.png](03-coverage.png) | Expanded event-logging quote and next action | Public illustrative assessment, not tenant analysis |
| [04-risks.png](04-risks.png) | Priorities, owners, and next actions; heatmap collapsed | Public fictional risk examples |
| [05-monitoring.png](05-monitoring.png) | GitHub/AWS connection controls and evidence-history action | Signed-in setup; no connector credentials supplied |
| [06-questionnaires.png](06-questionnaires.png) | Questionnaire review queue | Signed-in empty state; no answers approved |
| [07-framework-drift.png](07-framework-drift.png) | Framework version comparison controls | Signed-in tool; no comparison result claimed |
| [08-policies.png](08-policies.png) | Policy library and model-usage counters | Signed-in empty library; no generation or export performed |
| [09-trust-center.png](09-trust-center.png) | Platform safeguards and implementation disclosures | Public information, not a certification |
| [10-audit-share.png](10-audit-share.png) | Engagement Audit Hub with the shared navigation, theme controls, and square fact panels | Read-only fictional share; no additional evidence records |
| [11-ai-systems.png](11-ai-systems.png) | Registered AI inventory, draft system details, and registration form | Signed-in fictional AI record |
| [12-ai-audit-share.png](12-ai-audit-share.png) | AI-system Audit Hub in the current theme with explicit exclusions | Read-only draft record, not deployment approval |
| [13-dark-theme.png](13-dark-theme.png) | Complete homepage in dark mode | Public, fictional example |
| [14-public-demo.png](14-public-demo.png) | Assessment excerpts, AI example, and illustrative policy | Public read-only product tour |
| [15-mobile.png](15-mobile.png) | Homepage and navigation at a 390-pixel viewport | Public responsive layout |
| [16-navigation.png](16-navigation.png) | Expanded Platform menu | Public desktop navigation |

## What this refresh verified

The public UI review passed theme/contrast, five viewport widths, hover/keyboard navigation,
product-image loading, example disclosures, routes, and signed-out workspace checks. Added checks
require the new logo images, page title, browser icon, and branded sign-in/sign-up pages.
This refresh reused existing fictional assessment and AI records, filled an unsaved intake
preview, and created expiring engagement- and AI-system-scoped audit shares. It did not submit
new assessments or register more AI systems. Screenshots were taken after workspace content
and logo images had loaded.

The test organization contains records from earlier walkthroughs, so repeated LedgerPeak names
are separate test records, not distinct customers. No existing records were deleted for presentation.
Both Audit Hub report types use the current logo, navigation, sun/moon control,
theme palette, and square panels. Their screenshots were captured in a separate signed-out
browser, verifying that each report remains accessible through a valid share link without signing in;
it does not show the private workspace navigation or add editing controls. Print styling hides
navigation and uses a white report background.

The browser regression check covers the branded shared shell, light/dark themes, 1440/390/320-pixel
widths, and print styling on both loaded report types and the invalid-link state.

This pass did **not** run Ollama inference, connect GitHub/AWS, approve generated material, or
complete an audit. Empty states and pending/draft labels are preserved deliberately. Share URLs
expire and are not published here; the PNGs remain viewable after expiry.

## Reproduce the captures

From `apps/api`, run:

```powershell
python -m uv run python scripts/selenium_ui_review.py --base-url https://web-six-xi-53.vercel.app
python -m uv run python scripts/selenium_portfolio.py --headless
python -m uv run python scripts/selenium_portfolio.py --capture
```

The UI review saves public images to `.tmp-ui-checks/` at the repository root by default.
Use `home-light.png` for `01-overview.png`, `home-dark.png` for `13-dark-theme.png`,
`demo.png` for `14-public-demo.png`, `mobile.png` for `15-mobile.png`, `navigation.png`
for `16-navigation.png`, and `risks.png` for `04-risks.png`. The homepage preview is a
viewport-only capture; the numbered captures are full-page images except the menu viewport.
Inspect every image before replacing a tracked PNG, including account controls and lazy-loaded
product images. Keep the capture browser visible: minimized Chrome windows may pause capture.
The portfolio script waits for headings, which can appear before session/API
content; retake any loading states after the actual content is visible.

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
