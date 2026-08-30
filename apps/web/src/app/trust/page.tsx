import Link from "next/link";

const controls = [
  { id: "AC-3", title: "Access Enforcement", status: "Implemented", evidence: "PostgreSQL row-level security is enabled and forced on every tenant-owned table. Cross-tenant access is tested in CI." },
  { id: "SC-28", title: "Protection of Information at Rest", status: "Implemented", evidence: "Uploaded documents use AES-GCM envelope encryption with tenant-bound associated data and per-upload data keys." },
  { id: "SI-12", title: "Information Management and Retention", status: "Implemented", evidence: "A least-privilege database function removes expired uploads, engagements, and OSINT cache records according to the data policy." },
  { id: "SA-11", title: "Developer Testing and Evaluation", status: "Implemented", evidence: "CI runs tests, type checks, dependency audits, Bandit, Semgrep, and secret scanning. The current backend suite contains 60 passing tests." },
  { id: "CA-7", title: "Continuous Monitoring", status: "Implemented", evidence: "Read-only GitHub and AWS checks map live observations to controls and append immutable tenant-scoped evidence. No live customer connection is claimed yet." },
  { id: "AI-GRD-1", title: "Grounded Generation", status: "Implemented", evidence: "Generated control citations are rejected unless the cited ID was present in the exact retrieval context." },
] as const;

export default function TrustPage() {
  const implemented = controls.filter((control) => control.status === "Implemented").length;
  return (
    <main className="min-h-screen bg-slate-950 px-5 py-10 text-slate-100 sm:px-8 lg:py-16">
      <div className="mx-auto max-w-5xl">
        <Link href="/" className="text-sm font-medium text-cyan-300 hover:text-cyan-200">← Coverage demo</Link>
        <header className="mt-10 border-b border-slate-800 pb-10">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-400">Ruleset trust center</p>
          <h1 className="mt-4 max-w-3xl text-4xl font-semibold tracking-tight sm:text-6xl">The platform follows the controls it recommends.</h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-slate-400">This page distinguishes implemented safeguards from planned work. Claims link to evidence in the repository and automated test suite.</p>
          <div className="mt-8 inline-flex items-baseline gap-3 rounded-xl border border-emerald-400/20 bg-emerald-400/[0.06] px-5 py-4"><span className="text-3xl font-semibold text-emerald-300">{implemented}/{controls.length}</span><span className="text-sm text-emerald-100/70">controls implemented</span></div>
        </header>
        <section aria-labelledby="controls-heading" className="py-10">
          <h2 id="controls-heading" className="sr-only">Platform controls</h2>
          <div className="grid gap-4 md:grid-cols-2">
            {controls.map((control) => <article key={control.id} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6"><div className="flex items-start justify-between gap-4"><div><p className="font-mono text-sm font-semibold text-cyan-300">{control.id}</p><h3 className="mt-2 text-lg font-semibold">{control.title}</h3></div><span className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold ${control.status === "Implemented" ? "bg-emerald-400/10 text-emerald-300" : "bg-slate-700 text-slate-300"}`}>{control.status}</span></div><p className="mt-5 text-sm leading-6 text-slate-400">{control.evidence}</p></article>)}
          </div>
        </section>
        <footer className="border-t border-slate-800 pt-8 text-sm leading-6 text-slate-500">Draft platform evidence only. This is not a certification or independent audit opinion.</footer>
      </div>
    </main>
  );
}
