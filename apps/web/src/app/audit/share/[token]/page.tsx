"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
type Row = Record<string, unknown>;
type Share = {
  company: Row; policies: Row[]; coverage: Row[]; ai_system: Row | null;
  assessments: Row[]; objectives: Row[]; risks: Row[]; evaluations: Row[];
  approvals: Row[]; evidence: Row[]; incidents: Row[]; exclusions: string[];
};

const hiddenFields = new Set(["id", "org_id", "engagement_id", "ai_system_id"]);

function label(key: string) {
  return key.replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase());
}

function valueText(value: unknown): string {
  if (value === null || value === undefined || value === "") return "Not recorded";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (Array.isArray(value)) return value.length ? value.map(valueText).join(", ") : "None recorded";
  if (typeof value === "object") return Object.entries(value as Row).map(([key, item]) => `${label(key)}: ${valueText(item)}`).join(" · ");
  return String(value).replaceAll("_", " ");
}

function Facts({ row }: { row: Row }) {
  const entries = Object.entries(row).filter(([key]) => !hiddenFields.has(key));
  return <dl className="grid gap-x-8 sm:grid-cols-2">{entries.map(([key, value]) => <div key={key} className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)] gap-4 border-b border-zinc-800 py-3 text-sm"><dt className="text-slate-400">{label(key)}</dt><dd className="break-words font-medium text-slate-100">{valueText(value)}</dd></div>)}</dl>;
}

export default function AuditSharePage() {
  const { token } = useParams<{ token: string }>();
  const [share, setShare] = useState<Share | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${apiUrl}/audit/share/${encodeURIComponent(token)}`)
      .then((response) => {
        if (!response.ok) throw new Error("This audit link is invalid, expired, or revoked.");
        return response.json();
      })
      .then(setShare)
      .catch((reason: Error) => setError(reason.message));
  }, [token]);

  const groups: [string, Row[]][] = share ? [
    ["Policies", share.policies], ["Coverage evidence", share.coverage],
    ["Assessments", share.assessments], ["Objectives", share.objectives],
    ["Risks", share.risks], ["Evaluations", share.evaluations],
    ["Approvals", share.approvals], ["Evidence", share.evidence],
    ["Incidents", share.incidents],
  ] : [];
  const populated = groups.filter(([, rows]) => rows.length);
  const empty = groups.filter(([, rows]) => !rows.length).map(([title]) => title);
  const profile = share?.ai_system ?? share?.company;
  const title = share?.ai_system ? "AI system record" : "Company profile";

  return <main className="min-h-screen bg-black px-5 py-12 text-slate-100 sm:px-8"><div className="mx-auto max-w-[1500px]">
    <p className="text-xs font-semibold uppercase tracking-[0.24em] text-red-500">GRC Sentinel audit hub</p>
    <div className="mt-3 flex flex-wrap items-end justify-between gap-4"><div><h1 className="text-4xl font-semibold">Read-only compliance evidence</h1><p className="mt-2 text-sm text-slate-400">A scoped, external review package. Records cannot be changed from this page.</p></div><button type="button" onClick={() => window.print()} className="rounded-lg bg-teal-400 px-4 py-2 text-sm font-semibold text-black hover:bg-teal-300">Print report</button></div>
    {error && <p role="alert" className="mt-8 text-rose-300">{error}</p>}
    {!share && !error && <p className="mt-8 text-slate-400">Loading verified evidence…</p>}
    {share && profile && <>
      <section className="mt-8 rounded-2xl border border-zinc-800 bg-zinc-950 p-6"><h2 className="text-xl font-semibold">{title}</h2><p className="mt-1 text-sm text-slate-500">Friendly summary of the facts included in this share.</p><div className="mt-4"><Facts row={profile} /></div></section>
      {populated.length > 0 && <div className="mt-6 grid gap-5 xl:grid-cols-2">{populated.map(([groupTitle, rows]) => <Summary key={groupTitle} title={groupTitle} rows={rows} />)}</div>}
      {empty.length > 0 && <section className="mt-6 rounded-2xl border border-zinc-800 bg-zinc-950 p-6"><h2 className="text-lg font-semibold">No additional records</h2><p className="mt-2 text-sm text-slate-400">This share does not currently include {empty.join(", ").toLowerCase()}. That can be expected early in an assessment and is not itself a failed control.</p></section>}
      {share.exclusions.length > 0 && <section className="mt-6 rounded-2xl border border-amber-500/20 bg-amber-500/5 p-6"><h2 className="text-xl font-semibold">Explicit exclusions</h2><ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-amber-100">{share.exclusions.map((item) => <li key={item}>{item}</li>)}</ul></section>}
      <details className="mt-6 rounded-xl border border-zinc-800 bg-zinc-950"><summary className="cursor-pointer px-5 py-4 text-sm font-medium text-teal-300">Technical record (JSON)</summary><pre className="max-h-[32rem] overflow-auto border-t border-zinc-800 p-5 text-xs text-slate-400">{JSON.stringify(share, null, 2)}</pre></details>
    </>}
  </div></main>;
}

function Summary({ title, rows }: { title: string; rows: Row[] }) {
  return <section className="rounded-2xl border border-zinc-800 bg-zinc-950 p-6"><h2 className="text-xl font-semibold">{title} <span className="text-teal-300">{rows.length}</span></h2><div className="mt-4 space-y-4">{rows.map((row, index) => <article key={String(row.id ?? index)} className="rounded-xl border border-zinc-800 bg-black/40 px-4"><Facts row={row} /></article>)}</div></section>;
}
