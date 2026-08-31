import { CoverageMatrix, type CoverageRow } from "../components/coverage-matrix";
import Link from "next/link";
import { AuthControls } from "../components/auth-controls";
import { LiveIntake } from "../components/live-intake";

// Fintech crosswalk identifiers are sourced from the installed SCF 2026.2 catalog.
const rows = [
  { control: "AC-2", title: "Account Management", frameworks: ["SOC 2 CC6.1", "PCI DSS 8.2.4"], status: "covered", evidence: "Payment-platform access is reviewed quarterly by the system owner.", gap: "" },
  { control: "IA-2", title: "Identification and Authentication", frameworks: ["SOC 2 CC6.1", "PCI DSS 8.3.3"], status: "covered", evidence: "Multi-factor authentication is required for every privileged payment-system account.", gap: "" },
  { control: "AU-2", title: "Event Logging", frameworks: ["SOC 2 CC7.2", "PCI DSS 10.4.1"], status: "partial", evidence: "Authentication and payment-administration events are retained for 30 days.", gap: "Define alerting ownership and extend retention to the approved period." },
  { control: "SC-28", title: "Protection at Rest", frameworks: ["SOC 2 CC6.7", "PCI DSS 3.5"], status: "covered", evidence: "Stored payment data uses envelope encryption with tenant-bound keys.", gap: "" },
  { control: "IR-4", title: "Incident Handling", frameworks: ["SOC 2 CC7.4", "PCI DSS 12.10"], status: "missing", evidence: "", gap: "Create a payment-security incident procedure with roles, severity levels, and testing cadence." },
  { control: "SI-12", title: "Information Management and Retention", frameworks: ["SOC 2 C1.2", "PCI DSS 3.2.1"], status: "partial", evidence: "Payment records expire according to a documented retention schedule.", gap: "Document legal holds, deletion evidence, and annual review ownership." },
] satisfies CoverageRow[];

const perimeter = [
  { name: "GLBA Safeguards Rule", kind: "US federal regulation", scope: "FTC-covered financial institution handling customer information", source: "FTC", href: "https://www.ftc.gov/legal-library/browse/rules/safeguards-rule" },
  { name: "PCI DSS 4.0.1", kind: "Contractual industry standard", scope: "Stores, processes, or transmits payment account data", source: "PCI SSC", href: "https://www.pcisecuritystandards.org/document_library/" },
  { name: "SEC Regulation S-P", kind: "US federal securities rule", scope: "Covered broker-dealer, fund, adviser, funding portal, or transfer agent", source: "SEC", href: "https://www.sec.gov/rules-regulations/2024/06/s7-05-23" },
  { name: "FINRA Rule 4370", kind: "SRO rule", scope: "FINRA member firm", source: "FINRA", href: "https://www.finra.org/rules-guidance/key-topics/business-continuity-planning" },
  { name: "NYDFS Part 500", kind: "New York regulation", scope: "Entity covered by a NYDFS authorization", source: "NYDFS", href: "https://www.dfs.ny.gov/industry_guidance/cybersecurity" },
  { name: "SOX Section 404", kind: "Reporting and audit requirement", scope: "Company subject to Exchange Act periodic reporting", source: "SEC", href: "https://www.sec.gov/rules-regulations/2003/03/managements-report-internal-control-over-financial-reporting-certification-disclosure-exchange-act" },
  { name: "CCPA / CPRA", kind: "California privacy law", scope: "For-profit business meeting statutory thresholds and processing California personal information", source: "CPPA", href: "https://cppa.ca.gov/faq" },
  { name: "DORA", kind: "EU regulation", scope: "Financial entity within Regulation (EU) 2022/2554", source: "EUR-Lex", href: "https://eur-lex.europa.eu/legal-content/EN/LSU/?uri=CELEX:32022R2554" },
  { name: "MAS TRM Notices", kind: "Singapore regulatory notices", scope: "Financial institution category named in an applicable MAS Notice", source: "MAS", href: "https://www.mas.gov.sg/-/media/mas-media-library/regulation/faqs/trpd/faqs---notice-on-technology-risk-management/faqs---notice-on-trm/faq---notice-on-technology-risk-management.pdf" },
];

export default function Home() {
  return (
    <main className="min-h-screen bg-black text-slate-100">
      <div className="mx-auto max-w-[1600px] px-5 py-8 sm:px-8 lg:py-12">
        <header className="mb-10 flex flex-col gap-6 border-b border-zinc-800 pb-8 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="mb-3 text-xs font-semibold uppercase tracking-[0.24em] text-red-500">GRC Sentinel / Demo engagement</p>
            <h1 className="text-3xl font-semibold tracking-tight sm:text-5xl">Control coverage, with proof.</h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-slate-400">A deterministic evidence-gap analysis for LedgerPeak Payments. Every coverage claim links to an exact quote from the reviewed policy.</p>
          </div>
          <div className="flex flex-wrap gap-3 text-sm lg:justify-end">
            <AuthControls />
            <Link href="/risks" className="rounded-full border border-red-500/30 px-4 py-2 font-medium text-red-400 hover:bg-red-500/10">Risk register</Link>
            <Link href="/monitoring" className="rounded-full border border-red-500/30 px-4 py-2 font-medium text-red-400 hover:bg-red-500/10">Monitoring</Link>
            <Link href="/questionnaires" className="rounded-full border border-red-500/30 px-4 py-2 font-medium text-red-400 hover:bg-red-500/10">Questionnaires</Link>
            <Link href="/framework-drift" className="rounded-full border border-red-500/30 px-4 py-2 font-medium text-red-400 hover:bg-red-500/10">Framework drift</Link>
            <Link href="/policies" className="rounded-full border border-red-500/30 px-4 py-2 font-medium text-red-400 hover:bg-red-500/10">Policies</Link>
            <Link href="/trust" className="rounded-full border border-red-500/30 px-4 py-2 font-medium text-red-400 hover:bg-red-500/10">Trust center</Link>
            <span className="rounded-full border border-zinc-700 px-4 py-2 text-slate-300">PCI DSS 4.0.1 + SOC 2</span>
            <span className="rounded-full bg-emerald-400/10 px-4 py-2 font-medium text-emerald-300">Analysis complete</span>
          </div>
        </header>
        {process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY && <LiveIntake />}
        <section className="mb-10" aria-labelledby="regulatory-perimeter">
          <div className="mb-5 max-w-3xl">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-red-500">Fintech scoping perimeter</p>
            <h2 id="regulatory-perimeter" className="mt-2 text-2xl font-semibold">Different authorities, kept deliberately separate.</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">The intake records confirmed scope facts for review. A card is not an applicability decision; only an approved versioned rule may create one.</p>
          </div>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {perimeter.map((item) => <article key={item.name} className="rounded-xl border border-zinc-800 bg-zinc-950 p-4"><p className="text-xs font-semibold uppercase tracking-wide text-red-400">{item.kind}</p><h3 className="mt-2 font-semibold">{item.name}</h3><p className="mt-2 text-sm leading-6 text-slate-400">{item.scope}</p><a className="mt-3 inline-block text-xs font-medium text-red-400 hover:text-red-300" href={item.href} target="_blank" rel="noreferrer">Official source: {item.source}</a></article>)}
          </div>
        </section>
        <CoverageMatrix rows={rows} />
      </div>
    </main>
  );
}
