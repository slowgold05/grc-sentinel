"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
type Share = { company: Record<string, unknown>; policies: Record<string, unknown>[]; coverage: Record<string, unknown>[] };

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

  return <main className="min-h-screen bg-black px-5 py-12 text-slate-100"><div className="mx-auto max-w-[1600px]"><p className="text-xs font-semibold uppercase tracking-[0.24em] text-red-500">Ruleset audit hub</p><h1 className="mt-3 text-4xl font-semibold">Read-only compliance evidence</h1>{error && <p role="alert" className="mt-8 text-rose-300">{error}</p>}{!share && !error && <p className="mt-8 text-slate-400">Loading verified evidence…</p>}{share && <><section className="mt-8 rounded-2xl border border-zinc-800 bg-zinc-950 p-6"><h2 className="text-xl font-semibold">Company profile</h2><pre className="mt-4 overflow-auto text-sm text-slate-300">{JSON.stringify(share.company, null, 2)}</pre></section><div className="mt-6 grid gap-5 md:grid-cols-2"><Summary title="Policies" count={share.policies.length} rows={share.policies} /><Summary title="Coverage evidence" count={share.coverage.length} rows={share.coverage} /></div></>}</div></main>;
}

function Summary({ title, count, rows }: { title: string; count: number; rows: Record<string, unknown>[] }) {
  return <section className="rounded-2xl border border-zinc-800 bg-zinc-950 p-6"><h2 className="text-xl font-semibold">{title} <span className="text-red-400">{count}</span></h2><div className="mt-4 space-y-3">{rows.map((row, index) => <pre key={String(row.id ?? index)} className="overflow-auto rounded-lg bg-black p-3 text-xs text-slate-400">{JSON.stringify(row, null, 2)}</pre>)}{!rows.length && <p className="text-sm text-slate-400">No records available.</p>}</div></section>;
}
