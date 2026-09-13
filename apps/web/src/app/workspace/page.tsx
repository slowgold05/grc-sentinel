import Link from "next/link";
import { LiveIntake } from "../../components/live-intake";
import { SessionWorkspace } from "../../components/session-workspace";

/** Entry point for real, organization-scoped assessments. */
export default function WorkspacePage() {
  return <main className="page-wrap">
    <header className="page-heading"><p className="eyebrow">Your workspace</p><h1>Company assessments</h1><p className="muted">Describe a company, review its scope, and inspect its policy evidence.</p></header>
    {process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
      ? <SessionWorkspace><LiveIntake /></SessionWorkspace>
      : <section className="surface p-6"><p>Account access is not configured in this build.</p><Link className="text-link mt-3 inline-block" href="/demo">Explore the public demo →</Link></section>}
  </main>;
}
