"use client";

import Link from "next/link";
import { useState } from "react";
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

const regimes = ["GLBA", "PCI DSS", "Regulation S-P", "FINRA 4370", "NYDFS 500", "SOX 404", "CCPA / CPRA", "DORA", "MAS TRM", "HIPAA", "ISO 27001", "SOC 2", "NIST 800-53", "NIST AI RMF", "ISO 42001"];

const plainLanguageSteps = [
  ["Describe the company", "Answer a short set of questions about the business, its customers, locations, and data."],
  ["See what needs review", "The rules engine narrows the relevant regulations and clearly marks anything needing expert confirmation."],
  ["Find the gaps", "Upload policies and connect evidence to see which safeguards are covered, incomplete, or missing."],
  ["Share the result", "Track fixes, govern AI systems, and prepare a readable workspace for reviewers and auditors."],
] as const;

export default function Home() {
  const [assessmentOpen, setAssessmentOpen] = useState(false);
  function startAssessment() {
    setAssessmentOpen(true);
    requestAnimationFrame(() => document.querySelector("#new-assessment")?.scrollIntoView({ behavior: "smooth" }));
  }

  return (
    <main className="bg-[#f5f7f9] px-5 py-6 text-slate-950 sm:px-8 lg:px-10 lg:py-8">
      <header className="border-b border-slate-200 pb-6">
        <div><p className="text-sm text-slate-500">LedgerPeak Payments</p><h1 className="mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">Compliance overview</h1></div>
      </header>

      <section className="hero-panel my-7 overflow-hidden rounded-3xl bg-[#111e27] text-white" aria-labelledby="platform-heading">
        <div className="grid lg:grid-cols-[minmax(0,0.9fr)_minmax(480px,1.1fr)]">
        <div className="flex flex-col justify-center p-7 sm:p-10 lg:p-12">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-300">Compliance, made understandable</p>
          <h2 id="platform-heading" className="mt-4 max-w-xl text-4xl font-semibold tracking-tight sm:text-5xl">Turn compliance work into a clear plan.</h2>
          <p className="mt-5 max-w-xl text-base leading-7 text-slate-300">GRC Sentinel helps a company understand which security and AI-governance requirements may matter, organize proof that safeguards exist, and show reviewers what still needs attention.</p>
          <div className="mt-7 flex flex-wrap gap-3"><button type="button" onClick={startAssessment} className="rounded-lg bg-[#4f7cff] px-5 py-3 text-sm font-semibold text-white hover:bg-[#3e69e8]">Start an assessment</button><a href="#how-it-works" className="rounded-lg border border-white/25 px-5 py-3 text-sm font-semibold text-white hover:bg-white/10">How it works</a></div>
          <p className="mt-5 text-xs leading-5 text-slate-400">Portfolio demonstration only. It supports structured review; it does not replace legal counsel, a qualified assessor, or formal certification.</p>
        </div>
        <div className="m-5 rounded-2xl border border-white/15 bg-[#182832] p-5 shadow-2xl lg:m-10 lg:ml-0" aria-label="Product preview">
          <div className="flex items-center justify-between border-b border-white/10 pb-4"><div><p className="text-xs text-slate-400">LedgerPeak Payments</p><h3 className="mt-1 font-semibold">Compliance overview</h3></div><span className="rounded-full bg-emerald-400/15 px-3 py-1 text-xs font-semibold text-emerald-300">Live program</span></div>
          <div className="mt-5 grid gap-3 sm:grid-cols-3">{[["Readiness", "74%"], ["Open risks", "3"], ["AI systems", "4"]].map(([label, value]) => <div key={label} className="rounded-xl bg-white/[0.06] p-4"><p className="text-xs text-slate-400">{label}</p><p className="mt-2 text-2xl font-semibold">{value}</p></div>)}</div>
          <div className="mt-4 rounded-xl bg-white/[0.06] p-4"><div className="flex justify-between text-xs"><span>Control coverage</span><span className="text-sky-300">18 of 24</span></div><div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10"><div className="h-full w-3/4 rounded-full bg-sky-400" /></div><div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs"><span className="rounded-lg bg-emerald-400/10 p-2 text-emerald-300">15 covered</span><span className="rounded-lg bg-amber-400/10 p-2 text-amber-200">3 partial</span><span className="rounded-lg bg-rose-400/10 p-2 text-rose-200">6 missing</span></div></div>
          <div className="mt-4 rounded-xl border border-white/10 p-4"><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Next action</p><p className="mt-2 text-sm font-medium">Review the incident response gap</p><p className="mt-1 text-xs text-slate-400">Owner: Security · High priority</p></div>
        </div>
        </div>
        <div className="framework-marquee border-t border-white/10 py-5" aria-label="Frameworks represented in GRC Sentinel">
          <div className="framework-marquee__track">{[0, 1].map((copy) => <div key={copy} className="framework-marquee__group" aria-hidden={copy === 1}>{regimes.map((regime) => <span key={`${copy}-${regime}`}>{regime}</span>)}</div>)}</div>
        </div>
      </section>

      <section id="how-it-works" className="py-8" aria-labelledby="how-heading">
        <div className="max-w-3xl"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#4f7cff]">What the platform does</p><h2 id="how-heading" className="mt-3 text-3xl font-semibold tracking-tight">A simpler path from questions to proof.</h2><p className="mt-3 text-base leading-7 text-slate-500">You do not need to be a lawyer or security engineer to begin. The platform guides the process and keeps expert decisions clearly separated.</p></div>
        <div className="mt-7 grid gap-4 md:grid-cols-2 xl:grid-cols-4">{plainLanguageSteps.map(([title, copy], index) => <article key={title} className="rounded-2xl border border-slate-200 bg-white p-5"><span className="grid size-8 place-items-center rounded-full bg-blue-50 text-sm font-bold text-[#4f7cff]">{index + 1}</span><h3 className="mt-5 font-semibold">{title}</h3><p className="mt-2 text-sm leading-6 text-slate-500">{copy}</p></article>)}</div>
        <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-950"><strong>Where human review fits:</strong> the system can organize regulatory scope, policies, controls, and evidence, but reviewer-gated rules remain visibly marked until a qualified person approves them.</div>
      </section>

      <section className="pb-7" aria-labelledby="program-status">
        <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
          <div><h2 id="program-status" className="text-lg font-semibold">Program status</h2><p className="mt-1 text-sm text-slate-500">A focused view of what needs attention now.</p></div>
          <button type="button" onClick={startAssessment} className="rounded-lg bg-[#4f7cff] px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-[#3e69e8]">New assessment</button>
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
