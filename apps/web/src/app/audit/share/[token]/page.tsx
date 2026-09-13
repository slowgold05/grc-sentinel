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
  return <dl className="audit-facts grid gap-x-8 md:grid-cols-2">{entries.map(([key, value]) => <div key={key} className="grid min-w-0 grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)] gap-4 border-b border-[var(--line)] py-3 text-sm"><dt className="muted break-words">{label(key)}</dt><dd className="min-w-0 break-words font-medium">{valueText(value)}</dd></div>)}</dl>;
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

  return <main className="page-wrap audit-report">
    <header className="page-heading"><div className="flex flex-wrap items-center justify-between gap-3"><p className="eyebrow">Sentinal / Audit Hub</p><span className="muted text-xs">READ-ONLY SHARE</span></div>
      <div className="flex flex-wrap items-end justify-between gap-4"><div><h1>Read-only compliance evidence</h1><p className="muted">A scoped, external review package. Records cannot be changed from this page.</p></div><button type="button" onClick={() => window.print()} className="primary-button">Print report</button></div>
    </header>
    {error && <p role="alert" className="surface border-l-4 border-l-[var(--danger)] p-5 text-[var(--danger)]">{error}</p>}
    {!share && !error && <p role="status" className="muted py-6">Loading verified evidence…</p>}
    {share && profile && <>
      <section className="surface p-5 sm:p-6"><p className="eyebrow mb-2">Shared record</p><h2 className="text-xl font-semibold">{title}</h2><p className="muted mt-1 text-sm">Only the facts included in this share. Scope facts are not legal determinations.</p><div className="mt-4"><Facts row={profile} /></div></section>
      {populated.length > 0 && <div className="mt-6 grid gap-5 xl:grid-cols-2">{populated.map(([groupTitle, rows]) => <Summary key={groupTitle} title={groupTitle} rows={rows} />)}</div>}
      {empty.length > 0 && <section className="surface mt-6 p-5 sm:p-6"><h2 className="text-lg font-semibold">No additional records</h2><p className="muted mt-2 text-sm leading-relaxed">This share does not currently include {empty.join(", ").toLowerCase()}. That can be expected early in an assessment and is not itself a failed control.</p></section>}
      {share.exclusions.length > 0 && <section className="surface mt-6 border-l-4 border-l-[var(--warning)] p-5 sm:p-6"><h2 className="text-lg font-semibold">Explicit exclusions</h2><ul className="muted mt-3 list-disc space-y-2 pl-5 text-sm">{share.exclusions.map((item) => <li key={item}>{item}</li>)}</ul></section>}
      <details className="surface mt-6"><summary className="text-link cursor-pointer px-5 py-4 text-sm">Technical record (JSON)</summary><pre className="muted max-h-[32rem] overflow-auto border-t border-[var(--line)] p-5 text-xs">{JSON.stringify(share, null, 2)}</pre></details>
    </>}
    <footer className="muted mt-8 border-t border-[var(--line)] pt-5 text-xs leading-relaxed">Portfolio prototype. Shared facts and records are not a certification or audit opinion. Generated material requires qualified human review.</footer>
  </main>;
}

function Summary({ title, rows }: { title: string; rows: Row[] }) {
  return <section className="surface min-w-0 p-5 sm:p-6"><h2 className="text-xl font-semibold">{title} <span className="text-[var(--accent)]">{rows.length}</span></h2><div className="mt-4 space-y-4">{rows.map((row, index) => <article key={String(row.id ?? index)}><Facts row={row} /></article>)}</div></section>;
}
