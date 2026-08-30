import Link from "next/link";
import { PolicyLibrary } from "../../components/policy-library";

export default function PoliciesPage() {
  return <main className="min-h-screen bg-slate-950 px-5 py-10 text-slate-100 sm:px-8"><div className="mx-auto max-w-5xl"><Link href="/" className="text-sm text-cyan-300">← Coverage</Link><p className="mt-8 text-xs font-semibold uppercase tracking-[0.24em] text-cyan-400">Policy library</p><h1 className="mt-3 text-4xl font-semibold">Verified policy exports</h1><p className="mt-4 max-w-2xl text-slate-400">Download auditor-readable drafts with deterministic control traceability. Professional review remains required.</p>{process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ? <PolicyLibrary /> : <p className="mt-8 text-amber-200">Configure Clerk to access tenant policies.</p>}</div></main>;
}
