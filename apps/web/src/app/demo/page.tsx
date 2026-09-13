import Link from "next/link";
import { DemoPreview } from "../../components/demo-preview";
import { DemoAISystem } from "../../components/demo-ai-system";
import { demoChecks } from "../../lib/demo";

/** A read-only walkthrough that never fetches or modifies tenant records. */
export default function DemoPage() {
  return <main className="page-wrap">
    <header className="page-heading"><p className="eyebrow">Public product tour</p><h1>Explore LedgerPeak Payments</h1><p className="muted">A fictional assessment you can inspect without signing in. All records below are illustrative.</p></header>
    <nav className="mb-6 flex flex-wrap gap-5 border-b border-[var(--line)] pb-4" aria-label="Demo sections"><a className="text-link" href="#assessment">Assessment</a><a className="text-link" href="#ai-system">AI system</a><a className="text-link" href="#policy">Policy example</a><Link className="text-link" href="/risks">Risk register →</Link></nav>
    <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(300px,.65fr)]">
      <section id="assessment"><h2 className="mb-2 text-xl font-semibold">From a policy to a reviewable gap</h2><p className="muted mb-5 text-sm leading-6">Open a check to see the example policy wording and next action. These are illustrative document checks, not legal determinations.</p>
        <div className="surface divide-y divide-[var(--line)]">{demoChecks.map((check) => <details key={check.title} className="p-5"><summary className="flex cursor-pointer items-center justify-between gap-4"><span className="font-medium">{check.title}</span><span className={check.status === "Covered" ? "status-success" : check.status === "Missing" ? "status-danger" : "status-warning"}>{check.status}</span></summary><div className="mt-4 text-sm leading-6"><h3 className="font-semibold">Example policy excerpt</h3><blockquote className="muted mt-2 border-l-2 border-[var(--accent)] pl-4">{check.quote || "No supporting policy excerpt in this fictional example."}</blockquote><p className="mt-4"><strong>Next action:</strong> {check.next}</p></div></details>)}</div>
      </section><DemoPreview />
    </div>
    <section id="ai-system" className="mt-10"><DemoAISystem /></section>
    <section id="policy" className="surface mt-6 p-5 sm:p-6"><p className="eyebrow">Illustrative policy extract · Human review required</p><h2 className="mt-2 text-xl font-semibold">Payment-platform access</h2><p className="muted mt-3 text-sm">This sample wording supplies the account-access example above. It is not a generated, approved policy or an audit result.</p><blockquote className="mt-5 border-l-2 border-[var(--accent)] pl-5 text-lg leading-8">{demoChecks[0].quote}</blockquote><p className="muted mt-5 text-sm">In a real assessment, uploaded policy text, its source, and the review decision remain linked in the workspace.</p><Link className="text-link mt-5 inline-block" href="/policies">Open the policy library →</Link></section>
    <footer className="mt-8 flex flex-wrap items-center justify-between gap-4 border-t border-[var(--line)] py-6"><p className="muted text-sm">Ready to start with your own company?</p><Link className="primary-button" href="/workspace">Open workspace</Link></footer>
  </main>;
}
