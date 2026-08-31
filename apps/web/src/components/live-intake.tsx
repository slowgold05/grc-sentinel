"use client";

import { useAuth } from "@clerk/nextjs";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { CoverageMatrix, type CoverageRow } from "./coverage-matrix";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Engagement = {
  id: string;
  company: { company_name: string; domain: string };
  regulations: string[];
  assurance_objectives: { framework: string; version: string; basis: string }[];
  expires_at: string;
};
type Readiness = { framework: string; version: string; total: number; covered: number; partial: number; missing: number; not_assessed: number };

export function LiveIntake() {
  const { getToken, userId } = useAuth();
  const [result, setResult] = useState("");
  const [error, setError] = useState("");
  const [engagements, setEngagements] = useState<Engagement[]>([]);
  const [coverage, setCoverage] = useState<CoverageRow[] | null>(null);
  const [auditShare, setAuditShare] = useState<{ url: string; token: string } | null>(null);
  const [readiness, setReadiness] = useState<Readiness[]>([]);

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
          assurance_objectives: [
            ["iso", "ISO 27001"],
            ["soc2", "SOC 2 TSC"],
            ["nist", "NIST SP 800-53"],
          ].filter(([field]) => form.get(field)).map(([, framework]) => ({
            framework,
            basis: form.get("assurance_basis"),
            target_date: form.get("target_date") || null,
            scope: form.get("assurance_scope") || "",
          })),
        }),
      });
      if (!response.ok) return setError("Could not create engagement");
      const payload = await response.json();
      const regulations = payload.determinations.map((item: { regulation: string }) => item.regulation);
      const objectives = payload.assurance_objectives.map((item: { framework: string }) => item.framework);
      setResult([...regulations.map((item: string) => `${item} applies`), ...objectives.map((item: string) => `${item} selected`)].join(" · ") || "No current rule or assurance objective matched");
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
      setResult(`Indexed ${payload.embedded_sections} section(s); local AI analysis is running`);
      const analysis = await fetch(
        `${apiUrl}/api/engagements/${engagementId}/uploads/${payload.id}/analyze`,
        { method: "POST", headers: { Authorization: `Bearer ${token}` } },
      );
      if (!analysis.ok) return setError("Upload succeeded, but local AI analysis failed");
      const analyzed = await analysis.json();
      setResult(`Analyzed ${analyzed.analyzed_controls} required control(s)`);
      await inspectCoverage(engagementId);
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

  async function inspectCoverage(engagementId: string) {
    const token = await getToken();
    if (!token) return;
    setError("");
    try {
      const response = await fetch(`${apiUrl}/api/engagements/${engagementId}/coverage`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) return setError("Could not load coverage results");
      const rows: CoverageRow[] = await response.json();
      setCoverage(rows);
      if (!rows.length) setResult("No gap-analysis results are stored for this engagement yet");
    } catch {
      setError("Could not reach the coverage API");
    }
  }

  async function createAuditShare(engagementId: string) {
    const token = await getToken();
    if (!token) return;
    try {
      const response = await fetch(`${apiUrl}/api/engagements/${engagementId}/audit-shares`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ expires_in_hours: 24 }),
      });
      if (!response.ok) return setError("Could not create audit share");
      const payload = await response.json();
      setAuditShare({
        url: `${window.location.origin}/audit/share/${payload.token}`,
        token: payload.token,
      });
    } catch {
      setError("Could not reach the audit-share API");
    }
  }

  async function inspectReadiness(engagementId: string) {
    const token = await getToken();
    if (!token) return;
    try {
      const response = await fetch(`${apiUrl}/api/engagements/${engagementId}/assurance-readiness`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) return setError("Could not load assurance readiness");
      setReadiness(await response.json());
    } catch {
      setError("Could not reach the assurance-readiness API");
    }
  }

  async function revokeAuditShare() {
    if (!auditShare) return;
    const token = await getToken();
    if (!token) return;
    try {
      const response = await fetch(`${apiUrl}/api/audit-shares/${auditShare.token}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) return setError("Could not revoke audit share");
      setAuditShare(null);
      setResult("Audit link revoked");
    } catch {
      setError("Could not reach the audit-share API");
    }
  }

  if (!userId) return null;
  return (
    <section className="mb-10 rounded-2xl border border-red-500/20 bg-red-500/[0.04] p-6" aria-labelledby="new-engagement">
      <h2 id="new-engagement" className="text-xl font-semibold">Start a live engagement</h2>
      <p className="mt-2 text-sm text-slate-400">Facts are evaluated by versioned rules, never by an LLM.</p>
      <form onSubmit={submit} className="mt-5 grid gap-3 sm:grid-cols-3">
        <input required name="company_name" maxLength={200} placeholder="Company name" className="rounded-lg border border-zinc-700 bg-black px-3 py-2" />
        <input required name="domain" placeholder="example.com" className="rounded-lg border border-zinc-700 bg-black px-3 py-2" />
        <input required name="employee_count" type="number" min="1" placeholder="Employees" className="rounded-lg border border-zinc-700 bg-black px-3 py-2" />
        <label className="flex items-center gap-2 text-sm"><input name="us" type="checkbox" /> Operates in the US</label>
        <label className="flex items-center gap-2 text-sm"><input name="phi" type="checkbox" /> Handles PHI</label>
        <label className="flex items-center gap-2 text-sm"><input name="email" type="checkbox" /> Sends external email</label>
        <fieldset className="grid gap-2 rounded-lg border border-zinc-700 p-3 sm:col-span-3"><legend className="px-2 text-sm font-semibold text-red-400">Contract and assurance objectives</legend><div className="flex flex-wrap gap-5"><label className="flex items-center gap-2 text-sm"><input name="soc2" type="checkbox" /> SOC 2 readiness</label><label className="flex items-center gap-2 text-sm"><input name="iso" type="checkbox" /> ISO 27001 readiness</label><label className="flex items-center gap-2 text-sm"><input name="nist" type="checkbox" /> NIST SP 800-53 alignment</label></div><div className="mt-2 grid gap-3 sm:grid-cols-3"><select name="assurance_basis" defaultValue="customer_contract" className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="customer_contract">Customer or contract</option><option value="company_strategy">Company strategy</option><option value="regulator_request">Regulator request</option></select><input name="target_date" type="date" aria-label="Target completion date" className="rounded-lg border border-zinc-700 bg-black px-3 py-2" /><input name="assurance_scope" maxLength={500} placeholder="Scope, e.g. Security criteria" className="rounded-lg border border-zinc-700 bg-black px-3 py-2" /></div></fieldset>
        <button className="rounded-lg bg-red-400 px-4 py-2 font-semibold text-slate-950 hover:bg-red-300 sm:col-span-3">Create and evaluate</button>
      </form>
      {result && <p className="mt-4 text-sm font-medium text-emerald-300">{result}</p>}
      {error && <p role="alert" className="mt-4 text-sm text-rose-300">{error}</p>}
      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        {engagements.map((engagement) => <article key={engagement.id} className="rounded-xl border border-zinc-800 bg-black/70 p-4"><h3 className="font-semibold">{engagement.company.company_name}</h3><p className="mt-2 text-sm text-slate-400">{engagement.company.domain} · {engagement.regulations.join(", ") || "No matched regulation"}</p>{engagement.assurance_objectives.length > 0 && <div className="mt-3 flex flex-wrap gap-2">{engagement.assurance_objectives.map((objective) => <span key={objective.framework} className="rounded-full bg-violet-400/10 px-2 py-1 text-xs text-violet-300">{objective.framework} · {objective.basis.replaceAll("_", " ")}</span>)}</div>}<label className="mt-3 block cursor-pointer text-sm font-medium text-red-400">Attach PDF or DOCX<input type="file" accept=".pdf,.docx" className="sr-only" onChange={(event) => { const file = event.target.files?.[0]; if (file) upload(engagement.id, file); }} /></label><button onClick={() => inspectPosture(engagement.id)} className="mt-3 block text-sm font-medium text-red-400 hover:text-red-300">Run passive posture check</button><button onClick={() => inspectCoverage(engagement.id)} className="mt-3 block text-sm font-medium text-red-400 hover:text-red-300">View coverage matrix</button><button onClick={() => inspectReadiness(engagement.id)} className="mt-3 block text-sm font-medium text-violet-300 hover:text-violet-200">View assurance readiness</button><button onClick={() => createAuditShare(engagement.id)} className="mt-3 block text-sm font-medium text-red-400 hover:text-red-300">Create 24-hour audit link</button><button onClick={() => remove(engagement.id)} className="mt-3 text-sm font-medium text-rose-300 hover:text-rose-200">Delete engagement</button></article>)}
      </div>
      {readiness.length > 0 && <section className="mt-8 grid gap-3 sm:grid-cols-3" aria-label="Assurance readiness">{readiness.map((item) => <article key={item.framework} className="rounded-xl border border-violet-400/20 bg-violet-400/[0.05] p-4"><h3 className="font-semibold text-violet-200">{item.framework} {item.version}</h3><p className="mt-3 text-2xl font-semibold">{item.total ? Math.round(((item.covered + item.partial * 0.5) / item.total) * 100) : 0}%</p><p className="mt-2 text-xs text-slate-400">{item.covered} covered · {item.partial} partial · {item.missing} missing · {item.not_assessed} not assessed</p></article>)}</section>}
      {auditShare && <div className="mt-5 break-all rounded-lg border border-emerald-400/20 p-3 text-sm text-emerald-300">Audit link: <a className="underline" href={auditShare.url}>{auditShare.url}</a><button type="button" onClick={revokeAuditShare} className="ml-4 text-rose-300">Revoke</button></div>}
      {coverage && coverage.length > 0 && <div className="mt-8"><CoverageMatrix rows={coverage} /></div>}
    </section>
  );
}
