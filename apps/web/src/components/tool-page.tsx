import Link from "next/link";
import { SessionWorkspace } from "./session-workspace";

/** Consistent tool heading and account entry, with a public tour beside the live workflow. */
export function ToolPage({ title, description, children, example }: { title: string; description: string; children: React.ReactNode; example?: React.ReactNode }) {
  return <main className="page-wrap">
    <header className="page-heading"><div className="flex flex-wrap items-center justify-between gap-3"><p className="eyebrow">Workspace</p><Link className="text-link text-sm" href="/demo">Explore example records →</Link></div><h1>{title}</h1><p className="muted">{description}</p></header>
    {example}
    {process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ? <SessionWorkspace>{children}</SessionWorkspace> : <p className="muted my-6">Account access is not configured. You can still explore the public demo.</p>}
  </main>;
}
