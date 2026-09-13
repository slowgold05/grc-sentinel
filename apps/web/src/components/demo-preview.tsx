import Link from "next/link";
import { demoChecks, demoCovered, demoPartial, demoMissing } from "../lib/demo";

/** A labeled preview using the same examples as the public tour. */
export function DemoPreview() {
  return <div className="demo-preview">
    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/20 pb-5">
      <div><p className="hero-muted text-sm">LedgerPeak Payments · Fictional company</p><h2 className="mt-1 text-xl font-semibold">Example workspace</h2></div>
      <span className="example-badge">Read-only demo</span>
    </div>
    <p className="hero-muted mt-6 text-sm">Document coverage</p>
    <div className="mt-2 flex items-baseline gap-3"><strong className="text-4xl">{demoCovered} / {demoChecks.length}</strong><span className="hero-muted text-sm">checks fully supported</span></div>
    <div className="mt-5 grid grid-cols-3 gap-2 text-sm">
      <div className="border border-white/20 p-3"><strong className="block text-lg">{demoCovered}</strong>Covered</div>
      <div className="border border-white/20 p-3"><strong className="block text-lg">{demoPartial}</strong>Partial</div>
      <div className="border border-white/20 p-3"><strong className="block text-lg">{demoMissing}</strong>Missing</div>
    </div>
    <p className="hero-muted mt-3 text-xs leading-5">Counts describe six fictional policy checks, not a compliance score.</p>
    <div className="mt-6 border-t border-white/20 pt-5"><p className="hero-muted text-xs uppercase tracking-wider">Next action</p><p className="mt-2 font-medium">Review the incident response gap</p><Link className="hero-link mt-3 inline-block" href="/demo#assessment">Inspect the example →</Link></div>
  </div>;
}
