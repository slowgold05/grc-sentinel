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

  return <main className="min-h-screen bg-black px-5 py-12 text-slate-100"><div className="mx-auto max-w-[1600px]"><p className="text-xs font-semibold uppercase tracking-[0.24em] text-red-500">GRC Sentinel audit hub</p><h1 className="mt-3 text-4xl font-semibold">Read-only compliance evidence</h1>{error && <p role="alert" className="mt-8 text-rose-300">{error}</p>}{!share && !error && <p className="mt-8 text-slate-400">Loading verified evidence…</p>}{share && <><section className="mt-8 rounded-2xl border border-zinc-800 bg-zinc-950 p-6"><h2 className="text-xl font-semibold">{share.ai_system ? "AI system record" : "Company profile"}</h2><pre className="mt-4 overflow-auto text-sm text-slate-300">{JSON.stringify(share.ai_system ?? share.company, null, 2)}</pre></section><div className="mt-6 grid gap-5 md:grid-cols-2">{groups.map(([title, rows]) => <Summary key={title} title={title} rows={rows} />)}</div>{share.exclusions.length > 0 && <section className="mt-6 rounded-2xl border border-amber-500/20 bg-amber-500/5 p-6"><h2 className="text-xl font-semibold">Explicit exclusions</h2><ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-amber-100">{share.exclusions.map((item) => <li key={item}>{item}</li>)}</ul></section>}</>}</div></main>;
}

function Summary({ title, rows }: { title: string; rows: Row[] }) {
  return <section className="rounded-2xl border border-zinc-800 bg-zinc-950 p-6"><h2 className="text-xl font-semibold">{title} <span className="text-red-400">{rows.length}</span></h2><div className="mt-4 space-y-3">{rows.map((row, index) => <pre key={String(row.id ?? index)} className="overflow-auto rounded-lg bg-black p-3 text-xs text-slate-400">{JSON.stringify(row, null, 2)}</pre>)}{!rows.length && <p className="text-sm text-slate-400">No records available.</p>}</div></section>;
}
