import { CoverageMatrix, type CoverageRow } from "../components/coverage-matrix";
import Link from "next/link";
import { AuthControls } from "../components/auth-controls";
import { LiveIntake } from "../components/live-intake";

const rows = [
  { control: "AC-2", title: "Account Management", frameworks: ["SOC 2 CC6.2", "ISO A.5.15"], status: "covered", evidence: "Access reviews are completed quarterly by the system owner.", gap: "" },
  { control: "IA-2", title: "Identification and Authentication", frameworks: ["SOC 2 CC6.1", "HIPAA 164.312(d)"], status: "covered", evidence: "Multi-factor authentication is required for every administrator.", gap: "" },
  { control: "AU-2", title: "Event Logging", frameworks: ["SOC 2 CC7.2", "HIPAA 164.312(b)"], status: "partial", evidence: "Authentication events are retained for 30 days.", gap: "Define alerting ownership and extend retention to the approved period." },
  { control: "SC-28", title: "Protection at Rest", frameworks: ["SOC 2 CC6.7", "HIPAA 164.312(a)(2)(iv)"], status: "covered", evidence: "Customer uploads use envelope encryption with tenant-bound keys.", gap: "" },
  { control: "IR-4", title: "Incident Handling", frameworks: ["SOC 2 CC7.4", "ISO A.5.26"], status: "missing", evidence: "", gap: "Create an incident response procedure with roles, severity levels, and testing cadence." },
  { control: "SI-12", title: "Information Management and Retention", frameworks: ["HIPAA 164.316(b)(2)"], status: "partial", evidence: "Uploaded documents expire after 90 days.", gap: "Document retention exceptions and annual review ownership." },
] satisfies CoverageRow[];

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8 lg:py-12">
        <header className="mb-10 flex flex-col gap-6 border-b border-slate-800 pb-8 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="mb-3 text-xs font-semibold uppercase tracking-[0.24em] text-cyan-400">Ruleset / Demo engagement</p>
            <h1 className="text-3xl font-semibold tracking-tight sm:text-5xl">Control coverage, with proof.</h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-slate-400">A deterministic gap analysis for Northstar Health. Every coverage claim links to an exact quote from the reviewed policy.</p>
          </div>
          <div className="flex gap-3 text-sm">
            <AuthControls />
            <Link href="/risks" className="rounded-full border border-cyan-400/30 px-4 py-2 font-medium text-cyan-300 hover:bg-cyan-400/10">Risk register</Link>
            <Link href="/trust" className="rounded-full border border-cyan-400/30 px-4 py-2 font-medium text-cyan-300 hover:bg-cyan-400/10">Trust center</Link>
            <span className="rounded-full border border-slate-700 px-4 py-2 text-slate-300">HIPAA + SOC 2</span>
            <span className="rounded-full bg-emerald-400/10 px-4 py-2 font-medium text-emerald-300">Analysis complete</span>
          </div>
        </header>
        {process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY && <LiveIntake />}
        <CoverageMatrix rows={rows} />
      </div>
    </main>
  );
}
