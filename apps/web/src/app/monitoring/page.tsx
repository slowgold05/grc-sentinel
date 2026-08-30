import Link from "next/link";
import { LiveMonitoring } from "../../components/live-monitoring";

export default function MonitoringPage() {
  return <main className="min-h-screen bg-slate-950 px-5 py-10 text-slate-100 sm:px-8"><div className="mx-auto max-w-6xl"><Link href="/" className="text-sm text-cyan-300">← Coverage</Link><p className="mt-8 text-xs font-semibold uppercase tracking-[0.24em] text-cyan-400">Continuous monitoring</p><h1 className="mt-3 text-4xl font-semibold">Policy says it. Systems prove it.</h1><p className="mt-4 max-w-2xl text-slate-400">Connect read-only GitHub or AWS access. Credentials are encrypted per tenant; every result is immutable evidence.</p>{process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ? <div className="mt-9"><LiveMonitoring /></div> : <p className="mt-9 rounded-xl border border-amber-400/20 p-5 text-amber-200">Configure Clerk to use live monitoring.</p>}</div></main>;
}
