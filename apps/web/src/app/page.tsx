"use client";

import Link from "next/link";
import { useState } from "react";
import { AuthControls } from "../components/auth-controls";
import { LiveIntake } from "../components/live-intake";

const metrics = [
  ["Control readiness", "74%", "6 controls need attention"],
  ["Open risks", "3", "1 high-priority item"],
  ["AI systems", "4", "1 review pending"],
] as const;

const work = [
  ["Review missing incident response control", "IR-4 · High priority", "/risks"],
  ["Complete AI system impact assessment", "Customer support copilot", "/ai-systems"],
  ["Collect current access-review evidence", "Due this week", "/monitoring"],
] as const;

export default function Home() {
  const [assessmentOpen, setAssessmentOpen] = useState(false);
  return (
    <main className="bg-[#f5f7f9] px-5 py-6 text-slate-950 sm:px-8 lg:px-10 lg:py-8">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-6">
        <div><p className="text-sm text-slate-500">LedgerPeak Payments</p><h1 className="mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">Compliance overview</h1></div>
        <div className="flex items-center gap-3 lg:hidden"><AuthControls /></div>
      </header>

      <section className="py-7" aria-labelledby="program-status">
        <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
          <div><h2 id="program-status" className="text-lg font-semibold">Program status</h2><p className="mt-1 text-sm text-slate-500">A focused view of what needs attention now.</p></div>
          <button type="button" onClick={() => { setAssessmentOpen(true); requestAnimationFrame(() => document.querySelector("#new-assessment")?.scrollIntoView({ behavior: "smooth" })); }} className="rounded-lg bg-[#5b45e0] px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-[#4933c7]">New assessment</button>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {metrics.map(([label, value, note]) => <article key={label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]"><p className="text-sm font-medium text-slate-500">{label}</p><p className="mt-3 text-3xl font-semibold tracking-tight">{value}</p><p className="mt-2 text-sm text-slate-500">{note}</p></article>)}
        </div>
      </section>

      <section className="grid gap-5 pb-7 xl:grid-cols-[minmax(0,1.4fr)_minmax(300px,0.6fr)]">
        <article className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6">
          <div className="flex items-center justify-between"><div><h2 className="font-semibold">Priority work</h2><p className="mt-1 text-sm text-slate-500">Three actions move the program forward.</p></div><Link href="/risks" className="text-sm font-semibold text-[#5b45e0]">View all</Link></div>
          <div className="mt-5 divide-y divide-slate-100">
            {work.map(([title, note, href], index) => <Link key={title} href={href} className="flex items-center gap-4 py-4 first:pt-0 last:pb-0"><span className={`size-2 rounded-full ${index === 0 ? "bg-rose-500" : index === 1 ? "bg-amber-400" : "bg-sky-500"}`} /><span className="min-w-0 flex-1"><span className="block text-sm font-medium">{title}</span><span className="mt-1 block text-xs text-slate-500">{note}</span></span><span className="text-slate-400">→</span></Link>)}
          </div>
        </article>
        <article className="rounded-2xl bg-[#17132f] p-6 text-white">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-violet-300">AI governance</p><h2 className="mt-3 text-xl font-semibold">Know every AI system in use.</h2><p className="mt-3 text-sm leading-6 text-slate-300">Inventory systems, assess risk, record approvals, and keep evidence connected.</p><Link href="/ai-systems" className="mt-6 inline-flex rounded-lg bg-white px-4 py-2.5 text-sm font-semibold text-[#17132f]">Open AI inventory</Link>
        </article>
      </section>

      {process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY && <details id="new-assessment" open={assessmentOpen} onToggle={(event) => setAssessmentOpen(event.currentTarget.open)} className="group mb-7 rounded-2xl border border-slate-200 bg-white">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-4 p-5 sm:p-6"><span><span className="block font-semibold">Start a company assessment</span><span className="mt-1 block text-sm text-slate-500">Profile the company first; regulatory questions appear only when relevant.</span></span><span className="rounded-lg bg-violet-50 px-3 py-2 text-sm font-semibold text-[#5b45e0] group-open:hidden">Start</span><span className="hidden text-sm font-medium text-slate-500 group-open:block">Close</span></summary>
        <div className="border-t border-slate-200 p-4 sm:p-6"><LiveIntake /></div>
      </details>}

      <section className="grid gap-4 pb-8 md:grid-cols-3">
        {[["Controls & evidence", "See coverage and gaps across the shared control set.", "/monitoring"], ["Audit workspace", "Prepare clear, reviewable evidence without raw data dumps.", "/trust"], ["Framework library", "Review scope, mappings, and framework drift when needed.", "/framework-drift"]].map(([title, copy, href]) => <Link key={title} href={href} className="rounded-2xl border border-slate-200 bg-white p-5 hover:border-violet-300"><h2 className="font-semibold">{title}</h2><p className="mt-2 text-sm leading-6 text-slate-500">{copy}</p><span className="mt-4 block text-sm font-semibold text-[#5b45e0]">Open →</span></Link>)}
      </section>
    </main>
  );
}
