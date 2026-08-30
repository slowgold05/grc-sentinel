"use client";

import { useAuth } from "@clerk/nextjs";
import { FormEvent, useCallback, useEffect, useState } from "react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Engagement = {
  id: string;
  company: { company_name: string; domain: string };
  regulations: string[];
  expires_at: string;
};

export function LiveIntake() {
  const { getToken, userId } = useAuth();
  const [result, setResult] = useState("");
  const [error, setError] = useState("");
  const [engagements, setEngagements] = useState<Engagement[]>([]);

  const refresh = useCallback(async () => {
    const token = await getToken();
    if (!token) return;
    const response = await fetch(`${apiUrl}/api/engagements`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error("Could not load engagements");
    setEngagements(await response.json());
  }, [getToken]);

  useEffect(() => {
    if (userId) refresh().catch((reason: Error) => setError(reason.message));
  }, [refresh, userId]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const form = new FormData(event.currentTarget);
    const token = await getToken();
    if (!token) return setError("Sign in and select an organization first");
    try {
      const response = await fetch(`${apiUrl}/api/engagements`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          company: {
            company_name: form.get("company_name"),
            domain: form.get("domain"),
            employee_count: Number(form.get("employee_count")),
            geos: form.get("us") ? ["us"] : [],
            data_types: form.get("phi") ? ["phi"] : [],
            sends_external_email: form.get("email") === "on",
          },
        }),
      });
      if (!response.ok) return setError("Could not create engagement");
      const payload = await response.json();
      setResult(
        payload.determinations.length
          ? `${payload.determinations.map((item: { regulation: string }) => item.regulation).join(", ")} applies`
          : "No current rule matched",
      );
      await refresh();
    } catch {
      setError("Could not reach the intake API");
    }
  }

  async function remove(id: string) {
    const token = await getToken();
    if (!token) return;
    try {
      const response = await fetch(`${apiUrl}/api/engagements/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) return setError("Could not delete engagement");
      await refresh();
    } catch {
      setError("Could not reach the intake API");
    }
  }

  async function upload(engagementId: string, file: File) {
    const token = await getToken();
    if (!token) return;
    setError("");
    try {
      const response = await fetch(`${apiUrl}/api/engagements/${engagementId}/uploads`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/octet-stream",
          "X-Filename": file.name,
        },
        body: file,
      });
      if (!response.ok) return setError("Upload rejected; use a valid PDF or DOCX under 20 MiB");
      const payload = await response.json();
      setResult(`Encrypted upload stored with ${payload.sections} parsed section(s)`);
    } catch {
      setError("Could not reach the upload API");
    }
  }

  async function inspectPosture(engagementId: string) {
    const token = await getToken();
    if (!token) return;
    setError("");
    try {
      const response = await fetch(`${apiUrl}/api/engagements/${engagementId}/posture`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) return setError("Passive posture check was unavailable");
      const payload = await response.json();
      setResult(payload.observations.join(" · "));
    } catch {
      setError("Could not reach the posture API");
    }
  }

  if (!userId) return null;
  return (
    <section className="mb-10 rounded-2xl border border-cyan-400/20 bg-cyan-400/[0.04] p-6" aria-labelledby="new-engagement">
      <h2 id="new-engagement" className="text-xl font-semibold">Start a live engagement</h2>
      <p className="mt-2 text-sm text-slate-400">Facts are evaluated by versioned rules, never by an LLM.</p>
      <form onSubmit={submit} className="mt-5 grid gap-3 sm:grid-cols-3">
        <input required name="company_name" maxLength={200} placeholder="Company name" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" />
        <input required name="domain" placeholder="example.com" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" />
        <input required name="employee_count" type="number" min="1" placeholder="Employees" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" />
        <label className="flex items-center gap-2 text-sm"><input name="us" type="checkbox" /> Operates in the US</label>
        <label className="flex items-center gap-2 text-sm"><input name="phi" type="checkbox" /> Handles PHI</label>
        <label className="flex items-center gap-2 text-sm"><input name="email" type="checkbox" /> Sends external email</label>
        <button className="rounded-lg bg-cyan-300 px-4 py-2 font-semibold text-slate-950 hover:bg-cyan-200 sm:col-span-3">Create and evaluate</button>
      </form>
      {result && <p className="mt-4 text-sm font-medium text-emerald-300">{result}</p>}
      {error && <p role="alert" className="mt-4 text-sm text-rose-300">{error}</p>}
      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        {engagements.map((engagement) => <article key={engagement.id} className="rounded-xl border border-slate-800 bg-slate-950/70 p-4"><h3 className="font-semibold">{engagement.company.company_name}</h3><p className="mt-2 text-sm text-slate-400">{engagement.company.domain} · {engagement.regulations.join(", ") || "No matched regulation"}</p><label className="mt-3 block cursor-pointer text-sm font-medium text-cyan-300">Attach PDF or DOCX<input type="file" accept=".pdf,.docx" className="sr-only" onChange={(event) => { const file = event.target.files?.[0]; if (file) upload(engagement.id, file); }} /></label><button onClick={() => inspectPosture(engagement.id)} className="mt-3 block text-sm font-medium text-cyan-300 hover:text-cyan-200">Run passive posture check</button><button onClick={() => remove(engagement.id)} className="mt-3 text-sm font-medium text-rose-300 hover:text-rose-200">Delete engagement</button></article>)}
      </div>
    </section>
  );
}
