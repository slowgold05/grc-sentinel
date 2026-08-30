"use client";

import { useAuth } from "@clerk/nextjs";
import { FormEvent, useState } from "react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function LiveIntake() {
  const { getToken, userId } = useAuth();
  const [result, setResult] = useState("");
  const [error, setError] = useState("");

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
    } catch {
      setError("Could not reach the intake API");
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
    </section>
  );
}
