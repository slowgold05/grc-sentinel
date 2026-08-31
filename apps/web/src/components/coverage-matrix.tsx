"use client";

import { useMemo, useState } from "react";

export type CoverageStatus = "covered" | "partial" | "missing";

export interface CoverageRow {
  control: string;
  title: string;
  frameworks: string[];
  status: CoverageStatus;
  evidence: string;
  gap: string;
}

const statusStyle: Record<CoverageStatus, string> = {
  covered: "bg-emerald-400/10 text-emerald-300 ring-emerald-400/20",
  partial: "bg-amber-400/10 text-amber-300 ring-amber-400/20",
  missing: "bg-rose-400/10 text-rose-300 ring-rose-400/20",
};

export function CoverageMatrix({ rows }: { rows: CoverageRow[] }) {
  const [selected, setSelected] = useState(rows[0] ?? null);
  const counts = useMemo(
    () => Object.fromEntries((["covered", "partial", "missing"] as const).map((status) => [status, rows.filter((row) => row.status === status).length])) as Record<CoverageStatus, number>,
    [rows],
  );
  const score = rows.length ? Math.round(((counts.covered + counts.partial * 0.5) / rows.length) * 100) : 0;

  return (
    <section aria-labelledby="coverage-heading">
      <div className="mb-7 grid gap-3 sm:grid-cols-4">
        <Metric label="Coverage score" value={`${score}%`} accent />
        <Metric label="Covered" value={counts.covered.toString()} />
        <Metric label="Partial" value={counts.partial.toString()} />
        <Metric label="Missing" value={counts.missing.toString()} />
      </div>
      <div className="grid overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-950 shadow-2xl shadow-black/20 xl:grid-cols-[minmax(0,1.7fr)_minmax(320px,0.8fr)]">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[700px] border-collapse text-left">
            <caption className="sr-only">Required controls and policy coverage status</caption>
            <thead className="border-b border-zinc-800 bg-zinc-950 text-xs uppercase tracking-wider text-slate-500">
              <tr><th className="px-5 py-4">Control</th><th className="px-5 py-4">Cross-framework reach</th><th className="px-5 py-4">Status</th></tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {rows.map((row) => (
                <tr key={row.control} className={selected?.control === row.control ? "bg-red-500/[0.06]" : "hover:bg-slate-800/40"}>
                  <td className="p-0"><button type="button" onClick={() => setSelected(row)} className="w-full px-5 py-5 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-red-500"><span className="block font-mono text-sm font-semibold text-red-400">{row.control}</span><span className="mt-1 block text-sm text-slate-300">{row.title}</span></button></td>
                  <td className="px-5 py-5 text-sm text-slate-400">{row.frameworks.join(" · ")}</td>
                  <td className="px-5 py-5"><span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold capitalize ring-1 ring-inset ${statusStyle[row.status]}`}>{row.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <aside aria-live="polite" className="border-t border-zinc-800 bg-zinc-950 p-6 xl:border-l xl:border-t-0">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Evidence detail</p>
          {selected ? <><div className="mt-5 flex items-center justify-between gap-4"><h2 id="coverage-heading" className="text-xl font-semibold">{selected.control}</h2><span className={`rounded-full px-3 py-1 text-xs font-semibold capitalize ring-1 ring-inset ${statusStyle[selected.status]}`}>{selected.status}</span></div><p className="mt-1 text-sm text-slate-400">{selected.title}</p><div className="mt-7"><h3 className="text-sm font-semibold text-slate-200">Verified policy quote</h3><blockquote className="mt-3 border-l-2 border-red-500 pl-4 text-sm leading-6 text-slate-300">{selected.evidence || "No supporting evidence was found."}</blockquote></div>{selected.gap && <div className="mt-7 rounded-xl border border-amber-400/20 bg-amber-400/[0.06] p-4"><h3 className="text-sm font-semibold text-amber-200">Recommended next step</h3><p className="mt-2 text-sm leading-6 text-amber-100/70">{selected.gap}</p></div>}</> : <p className="mt-5 text-slate-400">No controls available.</p>}
        </aside>
      </div>
    </section>
  );
}

function Metric({ label, value, accent = false }: { label: string; value: string; accent?: boolean }) {
  return <div className={`rounded-xl border p-5 ${accent ? "border-red-500/30 bg-red-500/[0.07]" : "border-zinc-800 bg-zinc-950"}`}><p className="text-xs font-medium uppercase tracking-wider text-slate-500">{label}</p><p className={`mt-2 text-3xl font-semibold ${accent ? "text-red-400" : "text-slate-100"}`}>{value}</p></div>;
}
