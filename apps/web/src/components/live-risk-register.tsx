"use client";

import { useAuth } from "@clerk/nextjs";
import { FormEvent, useCallback, useEffect, useState } from "react";

type Risk = {
  id: string;
  title: string;
  description: string;
  likelihood: number;
  impact: number;
  score: number;
  status: string;
  treatment: string;
  control_ids: string[];
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function LiveRiskRegister() {
  const { getToken, isLoaded, userId } = useAuth();
  const [risks, setRisks] = useState<Risk[]>([]);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    const token = await getToken();
    if (!token) return;
    const response = await fetch(`${apiUrl}/api/risks`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error("Could not load tenant risks");
    setRisks(await response.json());
  }, [getToken]);

  useEffect(() => {
    if (userId) refresh().catch((reason: Error) => setError(reason.message));
  }, [refresh, userId]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const form = new FormData(event.currentTarget);
    const token = await getToken();
    if (!token) return setError("Sign in before creating a risk");
    try {
      const response = await fetch(`${apiUrl}/api/risks`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          title: form.get("title"),
          description: form.get("description"),
          likelihood: Number(form.get("likelihood")),
          impact: Number(form.get("impact")),
          control_ids: String(form.get("control_ids") ?? "").split(",").map((id) => id.trim()).filter(Boolean),
        }),
      });
      if (!response.ok) return setError("Could not create risk");
      event.currentTarget.reset();
      await refresh();
    } catch {
      setError("Could not reach the risk API");
    }
  }

  if (!isLoaded) return <p className="text-sm text-slate-400">Loading session…</p>;
  if (!userId) return <p className="text-sm text-slate-400">Sign in and select an organization to manage live tenant risks.</p>;

  return (
    <section className="mt-8 rounded-2xl border border-cyan-400/20 bg-cyan-400/[0.04] p-6" aria-labelledby="live-risks">
      <h2 id="live-risks" className="text-xl font-semibold">Live tenant risks</h2>
      <p className="mt-2 text-sm text-slate-400">Authenticated records from the RLS-protected API.</p>
      <form onSubmit={submit} className="mt-5 grid gap-3 sm:grid-cols-2">
        <input required name="title" maxLength={200} placeholder="Risk title" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" />
        <input required name="description" maxLength={10000} placeholder="Description" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" />
        <select name="likelihood" aria-label="Likelihood" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2">{[1, 2, 3, 4, 5].map((value) => <option key={value}>{value}</option>)}</select>
        <select name="impact" aria-label="Impact" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2">{[1, 2, 3, 4, 5].map((value) => <option key={value}>{value}</option>)}</select>
        <input name="control_ids" placeholder="Controls: IA-2, AC-2" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" />
        <button className="rounded-lg bg-cyan-300 px-4 py-2 font-semibold text-slate-950 hover:bg-cyan-200">Add risk</button>
      </form>
      {error && <p role="alert" className="mt-3 text-sm text-rose-300">{error}</p>}
      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        {risks.map((risk) => <article key={risk.id} className="rounded-xl border border-slate-800 bg-slate-950/70 p-4"><h3 className="font-semibold">{risk.title}</h3><p className="mt-2 text-sm text-slate-400">Score {risk.score} · {risk.status} · {risk.control_ids.join(", ") || "No mapped controls"}</p></article>)}
      </div>
    </section>
  );
}
