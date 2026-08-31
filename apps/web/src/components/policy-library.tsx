"use client";

import { useAuth } from "@clerk/nextjs";
import { useCallback, useEffect, useState } from "react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
type Policy = { id: string; policy_type: string; version: number; created_at: string };
type Usage = { input_tokens: number; output_tokens: number; cost_microusd: number };

export function PolicyLibrary() {
  const { getToken, userId } = useAuth();
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [error, setError] = useState("");
  const [usage, setUsage] = useState<Usage | null>(null);
  const load = useCallback(async () => {
    const token = await getToken();
    if (!token) return;
    const response = await fetch(`${apiUrl}/api/policies`, { headers: { Authorization: `Bearer ${token}` } });
    if (!response.ok) throw new Error("Could not load policies");
    setPolicies(await response.json());
    const usageResponse = await fetch(`${apiUrl}/api/model-usage`, { headers: { Authorization: `Bearer ${token}` } });
    if (usageResponse.ok) setUsage(await usageResponse.json());
  }, [getToken]);
  useEffect(() => { if (userId) load().catch((reason: Error) => setError(reason.message)); }, [load, userId]);

  async function download(policy: Policy) {
    const token = await getToken();
    if (!token) return;
    const response = await fetch(`${apiUrl}/api/policies/${policy.id}/docx`, { headers: { Authorization: `Bearer ${token}` } });
    if (!response.ok) return setError("Only fully verified policies can be exported");
    const url = URL.createObjectURL(await response.blob());
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${policy.policy_type.toLowerCase().replaceAll(" ", "-")}-v${policy.version}.docx`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return <div className="mt-8 grid gap-4 sm:grid-cols-2">{error && <p role="alert" className="text-rose-300 sm:col-span-2">{error}</p>}{usage && <div className="grid grid-cols-3 gap-3 sm:col-span-2"><Metric label="Input tokens" value={usage.input_tokens.toLocaleString()} /><Metric label="Output tokens" value={usage.output_tokens.toLocaleString()} /><Metric label="LLM cost" value={`$${(usage.cost_microusd / 1_000_000).toFixed(4)}`} /></div>}{policies.map((policy) => <article key={policy.id} className="rounded-2xl border border-zinc-800 bg-zinc-950 p-6"><h2 className="text-xl font-semibold">{policy.policy_type}</h2><p className="mt-2 text-sm text-slate-400">Version {policy.version} · {new Date(policy.created_at).toLocaleDateString()}</p><button onClick={() => download(policy)} className="mt-5 rounded-lg bg-red-400 px-4 py-2 font-semibold text-slate-950">Download verified DOCX</button></article>)}{!policies.length && !error && <p className="text-slate-400">No generated policies are stored yet.</p>}</div>;
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-4"><p className="text-xs uppercase text-slate-500">{label}</p><p className="mt-2 text-xl font-semibold text-red-400">{value}</p></div>;
}
