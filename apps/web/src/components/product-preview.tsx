import Link from "next/link";
import { demoChecks, demoCovered, demoPartial, demoMissing } from "../lib/demo";

/** Compact illustrative workspace, derived from the public tour's existing records. */
export function ProductPreview() {
  return <div className="product-preview" aria-label="Illustrative LedgerPeak workspace">
    <div className="preview-title"><span className="preview-mark" aria-hidden>S</span><div><strong>LedgerPeak Payments</strong><span>Example workspace · Fictional records</span></div><span className="preview-label">READ-ONLY</span></div>
    <div className="preview-body">
      <div className="preview-overview"><p className="preview-kicker">DOCUMENT COVERAGE</p><div className="preview-fraction"><strong>{demoCovered}</strong><span>/ {demoChecks.length} checks supported</span></div><div className="preview-bar" aria-hidden>{demoChecks.map((check, index) => <i key={index} data-status={check.status} />)}</div><div className="preview-counts"><span>{demoCovered} covered</span><span>{demoPartial} partial</span><span>{demoMissing} missing</span></div></div>
      <div className="preview-checks">{demoChecks.map((check) => <div key={check.title}><span>{check.title}</span><span className="preview-status" data-status={check.status}>{check.status}</span></div>)}</div>
      <div className="preview-evidence"><p className="preview-kicker">FROM THE EXAMPLE POLICY</p><blockquote>“{demoChecks[0].quote}”</blockquote><Link href="/demo#assessment">Inspect the supporting text <span aria-hidden>→</span></Link></div>
    </div>
    <div className="preview-footer"><span>Illustrative document checks. Not a compliance score.</span><span aria-hidden>→</span></div>
  </div>;
}
