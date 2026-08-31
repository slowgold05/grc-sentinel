"use client";

import { useAuth } from "@clerk/nextjs";
import { useCallback, useEffect, useState } from "react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
type Framework = { id: string; name: string; version: string };
type Impact = { drift: { added: string[]; removed: string[]; changed: string[] }; statements: { statement_id: string; text: string; control_ids: string[] }[] };

export function FrameworkImpact() {
  const { getToken, userId } = useAuth();
  const [frameworks, setFrameworks] = useState<Framework[]>([]);
  const [impact, setImpact] = useState<Impact | null>(null);
  const [error, setError] = useState("");
  const authorizedFetch = useCallback(async (path: string) => {
    const token = await getToken();
    if (!token) throw new Error("Sign in and select an organization first");
    return fetch(`${apiUrl}${path}`, { headers: { Authorization: `Bearer ${token}` } });
  }, [getToken]);

  useEffect(() => { if (userId) authorizedFetch("/api/frameworks").then((response) => response.json()).then(setFrameworks).catch(() => setError("Could not load frameworks")); }, [authorizedFetch, userId]);

  async function compare(form: FormData) {
    setError("");
    const response = await authorizedFetch(`/api/framework-drift?old=${form.get("old")}&new=${form.get("new")}`);
    if (!response.ok) return setError("Choose two versions of the same framework");
    setImpact(await response.json());
  }

  return <div className="mt-8"><form action={compare} className="grid gap-3 rounded-2xl border border-zinc-800 bg-zinc-950 p-6 sm:grid-cols-2"><select required name="old" className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">Previous version</option>{frameworks.map((item) => <option key={item.id} value={item.id}>{item.name} {item.version}</option>)}</select><select required name="new" className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">Current version</option>{frameworks.map((item) => <option key={item.id} value={item.id}>{item.name} {item.version}</option>)}</select><button className="rounded-lg bg-red-400 px-4 py-2 font-semibold text-slate-950 sm:col-span-2">Compare and find affected policies</button></form>{error && <p role="alert" className="mt-4 text-rose-300">{error}</p>}{impact && <div className="mt-6 grid gap-4 md:grid-cols-3"><Metric label="Added" values={impact.drift.added} /><Metric label="Changed" values={impact.drift.changed} /><Metric label="Removed" values={impact.drift.removed} /><section className="md:col-span-3"><h2 className="text-xl font-semibold">Affected statements</h2>{impact.statements.map((item) => <article key={item.statement_id} className="mt-3 rounded-xl border border-zinc-800 p-4"><p>{item.text}</p><p className="mt-2 text-xs text-red-400">{item.control_ids.join(", ")}</p></article>)}{!impact.statements.length && <p className="mt-3 text-slate-400">No tenant policy statements cite the changed controls.</p>}</section></div>}</div>;
}

function Metric({ label, values }: { label: string; values: string[] }) {
  return <section className="rounded-xl border border-zinc-800 bg-zinc-950 p-5"><h2 className="font-semibold">{label} <span className="text-red-400">{values.length}</span></h2><p className="mt-2 text-sm text-slate-400">{values.join(", ") || "None"}</p></section>;
}
