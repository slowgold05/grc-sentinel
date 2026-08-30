"use client";

import { useAuth } from "@clerk/nextjs";
import { FormEvent, useState } from "react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
type Provider = "github" | "aws";
type Run = { test_id: string; result: { status: "pass" | "fail" | "error"; observed: object } };

export function LiveMonitoring() {
  const { getToken } = useAuth();
  const [message, setMessage] = useState("");
  const [runs, setRuns] = useState<Run[]>([]);

  async function request(path: string, init: RequestInit) {
    const token = await getToken();
    if (!token) throw new Error("Sign in and select an organization first");
    const response = await fetch(`${apiUrl}${path}`, {
      ...init,
      headers: { ...init.headers, Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error((await response.json()).detail ?? "Request failed");
    return response;
  }

  async function connect(event: FormEvent<HTMLFormElement>, provider: Provider) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const payload = provider === "github"
      ? { provider, organization: form.get("organization"), token: form.get("token"), scopes: [] }
      : { provider, role_arn: form.get("role_arn"), external_id: form.get("external_id"), region: form.get("region"), scopes: [] };
    try {
      await request("/api/connections", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      event.currentTarget.reset();
      setMessage(`${provider.toUpperCase()} connection encrypted and saved`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Connection failed");
    }
  }

  async function run(provider: Provider) {
    setMessage(`Running ${provider.toUpperCase()} checks…`);
    try {
      const response = await request(`/api/connections/${provider}/run`, { method: "POST" });
      setRuns(await response.json());
      setMessage("Immutable evidence recorded");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Checks failed");
    }
  }

  async function disconnect(provider: Provider) {
    try {
      await request(`/api/connections/${provider}`, { method: "DELETE" });
      setMessage(`${provider.toUpperCase()} disconnected and credentials deleted`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Disconnect failed");
    }
  }

  return <>
    <div className="grid gap-5 lg:grid-cols-2">
      <Connector title="GitHub" onSubmit={(event) => connect(event, "github")}>
        <input required name="organization" placeholder="Organization slug" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" />
        <input required name="token" type="password" autoComplete="off" placeholder="Read-only token" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" />
        <Actions provider="github" run={run} disconnect={disconnect} />
      </Connector>
      <Connector title="AWS" onSubmit={(event) => connect(event, "aws")}>
        <input required name="role_arn" placeholder="Read-only IAM role ARN" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" />
        <input required name="external_id" type="password" autoComplete="off" placeholder="External ID" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" />
        <input required name="region" placeholder="us-east-1" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" />
        <Actions provider="aws" run={run} disconnect={disconnect} />
      </Connector>
    </div>
    {message && <p role="status" className="mt-6 text-sm text-cyan-300">{message}</p>}
    {runs.length > 0 && <div className="mt-8 grid gap-3 sm:grid-cols-3">{runs.map((item) => <article key={item.test_id} className="rounded-xl border border-slate-800 bg-slate-900 p-4"><p className="font-mono text-xs text-slate-400">{item.test_id}</p><p className="mt-2 font-semibold uppercase text-cyan-300">{item.result.status}</p><pre className="mt-3 overflow-auto text-xs text-slate-400">{JSON.stringify(item.result.observed, null, 2)}</pre></article>)}</div>}
  </>;
}

function Connector({ title, onSubmit, children }: { title: string; onSubmit: (event: FormEvent<HTMLFormElement>) => void; children: React.ReactNode }) {
  return <form onSubmit={onSubmit} className="grid gap-3 rounded-2xl border border-slate-800 bg-slate-900/60 p-6"><h2 className="text-xl font-semibold">{title}</h2>{children}</form>;
}

function Actions({ provider, run, disconnect }: { provider: Provider; run: (provider: Provider) => void; disconnect: (provider: Provider) => void }) {
  return <div className="flex flex-wrap gap-3"><button className="rounded-lg bg-cyan-300 px-4 py-2 font-semibold text-slate-950">Save encrypted connection</button><button type="button" onClick={() => run(provider)} className="rounded-lg border border-cyan-400/30 px-4 py-2 text-cyan-300">Run checks</button><button type="button" onClick={() => disconnect(provider)} className="px-3 py-2 text-rose-300">Disconnect</button></div>;
}
