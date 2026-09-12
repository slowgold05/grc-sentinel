"use client";

import { useAuth } from "@clerk/nextjs";
import { FormEvent, useCallback, useEffect, useState } from "react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Engagement = { id: string; company: { company_name: string } };
type AISystem = {
  id: string; engagement_id: string; name: string; description: string; owner: string;
  business_purpose: string; status: string; deployment_date: string | null;
  next_review_date: string | null; created_at: string;
  profile: {
    operator_roles: string[]; model_name: string; vendor: string; intended_users: string[];
    hosting_region: string | null; data_use_terms: string | null; subprocessors: string[];
    security_artifacts: string[]; contract_date: string | null; vendor_review_date: string | null;
    affected_persons: string[]; decision_impact: string; data_categories: string[];
    geographies: string[]; external_access: boolean; autonomy: string;
    tool_access: boolean; human_oversight: string;
  };
  vendor_review_gaps: string[];
};
type InternalRisk = { rating: string; score: number | null; fired_conditions: string[]; missing_facts: string[]; ruleset_version: number };
type AIObjective = { id: string; framework: string; source_version: string; objective_type: string; basis: string; scope: string };
type AIDashboard = { inventory: number; overdue_reviews: number; governance_blockers: number; failed_evaluations: number; open_incidents: number; expiring_exceptions: number };

const fieldClass = "rounded-lg border border-zinc-700 bg-black px-3 py-2 text-slate-100 placeholder:text-zinc-600";
const split = (value: FormDataEntryValue | null) => String(value ?? "").split(",").map((item) => item.trim()).filter(Boolean);

function StatusBadge({ status }: { status: string }) {
  const tone = status === "suspended" ? "bg-amber-400/10 text-amber-300" : status === "retired" ? "bg-zinc-700 text-zinc-300" : "bg-red-400/10 text-red-300";
  return <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${tone}`}>{status.replaceAll("_", " ")}</span>;
}

export function AISystemInventory() {
  const { getToken, isLoaded, userId } = useAuth();
  const [systems, setSystems] = useState<AISystem[]>([]);
  const [engagements, setEngagements] = useState<Engagement[]>([]);
  const [selected, setSelected] = useState<AISystem | null>(null);
  const [internalRisk, setInternalRisk] = useState<InternalRisk | null>(null);
  const [objectives, setObjectives] = useState<AIObjective[]>([]);
  const [dashboard, setDashboard] = useState<AIDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [shareUrl, setShareUrl] = useState("");

  const request = useCallback(async (path: string, init?: RequestInit) => {
    const token = await getToken();
    if (!token) throw new Error("Sign in and select an organization first");
    const response = await fetch(`${apiUrl}${path}`, {
      ...init,
      headers: { Authorization: `Bearer ${token}`, ...(init?.body ? { "Content-Type": "application/json" } : {}) },
    });
    if (!response.ok) {
      const detail = await response.json().catch(() => null);
      throw new Error(detail?.detail ?? "The AI inventory request failed");
    }
    return response.json();
  }, [getToken]);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [systemRows, engagementRows, dashboardRow] = await Promise.all([request("/api/ai-systems"), request("/api/engagements"), request("/api/ai-governance/dashboard")]);
      setSystems(systemRows);
      setEngagements(engagementRows);
      setDashboard(dashboardRow);
      setSelected((current) => current ? systemRows.find((row: AISystem) => row.id === current.id) ?? null : null);
      setError("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not load the AI inventory");
    } finally {
      setLoading(false);
    }
  }, [request]);

  useEffect(() => { if (userId) void refresh(); else setLoading(false); }, [refresh, userId]);
  useEffect(() => {
    setInternalRisk(null);
    setObjectives([]);
    if (selected) Promise.all([
      request(`/api/ai-systems/${selected.id}/internal-risk`),
      request(`/api/ai-systems/${selected.id}/objectives`),
    ]).then(([risk, rows]) => { setInternalRisk(risk); setObjectives(rows); }).catch((reason: Error) => setError(reason.message));
  }, [request, selected]);

  async function addObjective(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const form = new FormData(event.currentTarget);
    setSaving(true);
    try {
      const created = await request(`/api/ai-systems/${selected.id}/objectives`, { method: "POST", body: JSON.stringify({ framework: form.get("framework"), basis: form.get("basis"), scope: form.get("scope"), target_date: form.get("target_date") || null }) });
      setObjectives((rows) => [...rows, created]);
      event.currentTarget.reset();
      setError("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not select the objective");
    } finally {
      setSaving(false);
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    try {
      const created = await request("/api/ai-systems", {
        method: "POST",
        body: JSON.stringify({
          engagement_id: form.get("engagement_id"), name: form.get("name"), description: form.get("description"),
          owner: form.get("owner"), business_purpose: form.get("business_purpose"),
          deployment_date: form.get("deployment_date") || null, next_review_date: form.get("next_review_date") || null,
          profile: {
            operator_roles: [form.get("operator_role")], model_name: form.get("model_name"), vendor: form.get("vendor"),
            hosting_region: form.get("hosting_region") || null, data_use_terms: form.get("data_use_terms") || null,
            subprocessors: split(form.get("subprocessors")), security_artifacts: split(form.get("security_artifacts")),
            contract_date: form.get("contract_date") || null, vendor_review_date: form.get("vendor_review_date") || null,
            intended_users: split(form.get("intended_users")), affected_persons: split(form.get("affected_persons")),
            decision_impact: form.get("decision_impact"), data_categories: split(form.get("data_categories")),
            geographies: split(form.get("geographies")), external_access: form.get("external_access") === "on",
            autonomy: form.get("autonomy"), tool_access: form.get("tool_access") === "on",
            human_oversight: form.get("human_oversight"),
            decision_consequence: form.get("decision_consequence"), sensitive_data: form.get("sensitive_data") === "yes",
            autonomy_level: form.get("autonomy_level"), human_review_coverage: form.get("human_review_coverage"),
          },
        }),
      });
      formElement.reset();
      await refresh();
      setSelected(created);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not create the AI system");
    } finally {
      setSaving(false);
    }
  }

  async function changeStatus(status: string) {
    if (!selected) return;
    setSaving(true);
    try {
      const updated = await request(`/api/ai-systems/${selected.id}/status`, { method: "PATCH", body: JSON.stringify({ status }) });
      setSelected(updated);
      setSystems((rows) => rows.map((row) => row.id === updated.id ? updated : row));
      setError("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not update lifecycle state");
    } finally {
      setSaving(false);
    }
  }

  async function createAuditShare() {
    if (!selected) return;
    setSaving(true);
    try {
      const share = await request(`/api/ai-systems/${selected.id}/audit-shares`, { method: "POST", body: JSON.stringify({ expires_in_hours: 24 }) });
      setShareUrl(`${window.location.origin}/audit/share/${share.token}`);
      setError("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not create the audit share");
    } finally {
      setSaving(false);
    }
  }

  if (!isLoaded || loading) return <p className="mt-8 text-sm text-slate-400">Loading AI inventory&hellip;</p>;
  if (!userId) return <p className="mt-8 text-sm text-slate-400">Sign in and select an organization to manage AI systems.</p>;

  return (
    <section className="grid gap-8 py-10 xl:grid-cols-[minmax(22rem,0.8fr)_minmax(28rem,1.2fr)]" aria-label="AI system inventory">
      {dashboard && <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:col-span-2">{[["Inventory", dashboard.inventory], ["Governance blockers", dashboard.governance_blockers], ["Overdue reviews", dashboard.overdue_reviews], ["Failed evaluations", dashboard.failed_evaluations], ["Open incidents", dashboard.open_incidents], ["Exceptions expiring", dashboard.expiring_exceptions]].map(([label, value]) => <div key={label} className="rounded-xl border border-zinc-800 bg-zinc-950 p-4"><p className="text-xs uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-red-400">{value}</p></div>)}</div>}
      <div>
        <h2 className="text-xl font-semibold">Registered systems</h2>
        <p className="mt-2 text-sm text-slate-400">Tenant-scoped records protected by PostgreSQL row-level security.</p>
        {systems.length === 0 && <p className="mt-5 rounded-xl border border-dashed border-zinc-700 p-5 text-sm text-slate-400">No AI systems yet. Create the first inventory record.</p>}
        <div className="mt-5 space-y-3">
          {systems.map((system) => <button key={system.id} type="button" onClick={() => setSelected(system)} className="block w-full rounded-xl border border-zinc-800 bg-zinc-950 p-4 text-left hover:border-red-500/40 focus:outline-none focus:ring-2 focus:ring-red-500"><span className="flex items-start justify-between gap-3"><span className="font-semibold">{system.name}</span><StatusBadge status={system.status} /></span><span className="mt-2 block text-sm text-slate-400">{system.profile.vendor} / {system.profile.model_name}</span></button>)}
        </div>
        {selected && <article className="mt-5 rounded-xl border border-red-500/20 bg-red-500/[0.04] p-5" aria-live="polite"><div className="flex items-start justify-between gap-3"><h3 className="text-lg font-semibold">{selected.name}</h3><StatusBadge status={selected.status} /></div><dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2"><div><dt className="text-slate-500">Owner</dt><dd>{selected.owner}</dd></div><div><dt className="text-slate-500">Role</dt><dd>{selected.profile.operator_roles.join(", ")}</dd></div><div><dt className="text-slate-500">Purpose</dt><dd>{selected.business_purpose}</dd></div><div><dt className="text-slate-500">Decision impact</dt><dd>{selected.profile.decision_impact}</dd></div><div><dt className="text-slate-500">Data</dt><dd>{selected.profile.data_categories.join(", ") || "None recorded"}</dd></div><div><dt className="text-slate-500">Oversight</dt><dd>{selected.profile.human_oversight}</dd></div><div><dt className="text-slate-500">Hosting region</dt><dd>{selected.profile.hosting_region || "Not recorded"}</dd></div><div><dt className="text-slate-500">Vendor review</dt><dd>{selected.profile.vendor_review_date || "Not recorded"}</dd></div></dl>{selected.vendor_review_gaps.length > 0 && <p className="mt-3 text-xs text-amber-300">Vendor review gaps: {selected.vendor_review_gaps.join(", ").replaceAll("_", " ")}</p>}{internalRisk && <div className="mt-4 rounded-lg border border-zinc-800 bg-black/60 p-3 text-sm"><p><span className="text-slate-500">Internal risk v{internalRisk.ruleset_version}:</span> {internalRisk.rating.replaceAll("_", " ")}{internalRisk.score !== null && ` (${internalRisk.score})`}</p><p className="mt-1 text-xs text-slate-500">{internalRisk.missing_facts.length ? `Missing: ${internalRisk.missing_facts.join(", ")}` : `Fired: ${internalRisk.fired_conditions.join(", ") || "baseline"}`}</p><p className="mt-1 text-xs text-slate-500">Internal prioritization only; not a legal classification.</p></div>}<div className="mt-4 space-y-2">{objectives.map((item) => <p key={item.id} className="rounded-lg border border-violet-400/20 p-2 text-xs text-violet-200">{item.framework.replaceAll("_", " ")} {item.source_version} · {item.objective_type} · {item.basis.replaceAll("_", " ")}</p>)}</div><form onSubmit={addObjective} className="mt-4 grid gap-2"><select name="framework" aria-label="AI assurance framework" className={fieldClass}><option value="nist_ai_rmf">NIST AI RMF 1.0 · voluntary</option><option value="iso_42001">ISO/IEC 42001:2023 · certifiable</option><option value="singapore_model_ai_governance">Singapore Model AI Governance Framework · voluntary</option></select><select name="basis" aria-label="Objective basis" className={fieldClass}><option value="company_strategy">Company strategy</option><option value="customer_contract">Customer contract</option><option value="regulator_request">Regulator request</option></select><input required name="scope" maxLength={2000} placeholder="Objective scope" className={fieldClass} /><input name="target_date" type="date" aria-label="Objective target date" className={fieldClass} /><button disabled={saving} className="rounded-lg bg-violet-400 px-3 py-2 text-sm font-semibold text-black disabled:opacity-40">Select assurance objective</button></form><div className="mt-5 flex flex-wrap gap-2">{["in_review", "suspended", "retired"].map((status) => <button key={status} type="button" disabled={saving || selected.status === status} onClick={() => void changeStatus(status)} className="rounded-lg border border-zinc-700 px-3 py-2 text-xs font-medium hover:border-red-500 disabled:cursor-not-allowed disabled:opacity-40">Mark {status.replaceAll("_", " ")}</button>)}<button type="button" disabled={saving} onClick={() => void createAuditShare()} className="rounded-lg border border-red-500/50 px-3 py-2 text-xs font-medium text-red-300">Create 24-hour audit share</button></div>{shareUrl && <a className="mt-3 block break-all text-xs text-red-300 underline" href={shareUrl}>{shareUrl}</a>}<p className="mt-3 text-xs text-slate-500">Objectives are selected goals, never automatically applicable law. Approval and deployment require the protected human gate.</p></article>}
      </div>

      <form onSubmit={submit} className="grid gap-4 rounded-2xl border border-zinc-800 bg-zinc-950 p-6 sm:grid-cols-2" id="new-ai-system">
        <div className="sm:col-span-2"><h2 className="text-xl font-semibold">Register an AI system</h2><p className="mt-2 text-sm text-slate-400">Capture facts only; this form does not make a legal classification.</p></div>
        <label className="grid gap-1 text-sm">Engagement<select required name="engagement_id" className={fieldClass}><option value="">Select an engagement</option>{engagements.map((item) => <option key={item.id} value={item.id}>{item.company.company_name}</option>)}</select></label>
        <label className="grid gap-1 text-sm">System name<input required name="name" maxLength={200} className={fieldClass} /></label>
        <label className="grid gap-1 text-sm">Owner<input required name="owner" maxLength={200} className={fieldClass} /></label>
        <label className="grid gap-1 text-sm">Business purpose<input required name="business_purpose" maxLength={2000} className={fieldClass} /></label>
        <label className="grid gap-1 text-sm sm:col-span-2">Description<textarea required name="description" maxLength={10000} rows={2} className={fieldClass} /></label>
        <label className="grid gap-1 text-sm">Model<input required name="model_name" maxLength={200} className={fieldClass} /></label>
        <label className="grid gap-1 text-sm">Vendor<input required name="vendor" maxLength={200} className={fieldClass} /></label>
        <label className="grid gap-1 text-sm">Hosting region<input name="hosting_region" maxLength={200} placeholder="Local, US East, Singapore" className={fieldClass} /></label>
        <label className="grid gap-1 text-sm sm:col-span-2">Vendor data-use terms<textarea name="data_use_terms" maxLength={2000} rows={2} className={fieldClass} /></label>
        <label className="grid gap-1 text-sm">Subprocessors<input name="subprocessors" placeholder="Comma-separated; use None declared if confirmed" className={fieldClass} /></label>
        <label className="grid gap-1 text-sm">Security artifacts<input name="security_artifacts" placeholder="SOC 2 report, CAIQ" className={fieldClass} /></label>
        <label className="grid gap-1 text-sm">Contract date<input name="contract_date" type="date" className={fieldClass} /></label>
        <label className="grid gap-1 text-sm">Vendor review date<input name="vendor_review_date" type="date" className={fieldClass} /></label>
        <label className="grid gap-1 text-sm">Operator role<select name="operator_role" className={fieldClass}>{["deployer", "provider", "importer", "distributor", "product_manufacturer", "gpai_provider", "unknown"].map((role) => <option key={role}>{role}</option>)}</select></label>
        <label className="grid gap-1 text-sm">Intended users<input required name="intended_users" placeholder="Analysts, reviewers" className={fieldClass} /></label>
        <label className="grid gap-1 text-sm">Affected persons<input name="affected_persons" placeholder="Customers, applicants" className={fieldClass} /></label>
        <label className="grid gap-1 text-sm">Data categories<input name="data_categories" placeholder="Account data, support tickets" className={fieldClass} /></label>
        <label className="grid gap-1 text-sm">Geographies<input name="geographies" placeholder="US, Singapore" className={fieldClass} /></label>
        <label className="grid gap-1 text-sm">Autonomy<input required name="autonomy" maxLength={200} placeholder="Advisory only" className={fieldClass} /></label>
        <label className="grid gap-1 text-sm">Decision consequence<select required name="decision_consequence" className={fieldClass}>{["minimal", "material", "significant", "severe"].map((value) => <option key={value}>{value}</option>)}</select></label>
        <label className="grid gap-1 text-sm">Autonomy level<select required name="autonomy_level" className={fieldClass}>{["none", "assistive", "bounded", "autonomous"].map((value) => <option key={value}>{value}</option>)}</select></label>
        <label className="grid gap-1 text-sm">Human review coverage<select required name="human_review_coverage" className={fieldClass}>{["every_output", "sampled", "exception_only", "none"].map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}</select></label>
        <label className="grid gap-1 text-sm">Sensitive data<select required name="sensitive_data" className={fieldClass}><option value="no">No</option><option value="yes">Yes</option></select></label>
        <label className="grid gap-1 text-sm sm:col-span-2">Decision impact<textarea required name="decision_impact" maxLength={1000} rows={2} className={fieldClass} /></label>
        <label className="grid gap-1 text-sm sm:col-span-2">Human oversight<textarea required name="human_oversight" maxLength={2000} rows={2} className={fieldClass} /></label>
        <label className="grid gap-1 text-sm">Deployment date<input name="deployment_date" type="date" className={fieldClass} /></label>
        <label className="grid gap-1 text-sm">Next review date<input name="next_review_date" type="date" className={fieldClass} /></label>
        <label className="flex items-center gap-2 text-sm"><input name="external_access" type="checkbox" /> External users can access it</label>
        <label className="flex items-center gap-2 text-sm"><input name="tool_access" type="checkbox" /> Can invoke tools or actions</label>
        {engagements.length === 0 && <p className="text-sm text-amber-300 sm:col-span-2">Create an engagement on the coverage page before registering an AI system.</p>}
        <button disabled={saving || engagements.length === 0} className="rounded-lg bg-red-400 px-4 py-2 font-semibold text-black hover:bg-red-300 disabled:cursor-not-allowed disabled:opacity-40 sm:col-span-2">{saving ? "Saving…" : "Register system"}</button>
        {error && <p role="alert" className="text-sm text-rose-300 sm:col-span-2">{error}</p>}
      </form>
    </section>
  );
}
