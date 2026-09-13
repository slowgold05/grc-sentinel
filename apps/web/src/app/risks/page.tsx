import { LiveRiskRegister } from "../../components/live-risk-register";
import { ToolPage } from "../../components/tool-page";
import { demoRisks } from "../../lib/demo";

/** Lead with actionable example risks; keep the heatmap available on demand. */
export default function RisksPage() {
  return <ToolPage title="Risk register" description="Review priorities, ownership, and the next action for each risk." example={<>
    <section className="surface mb-5" aria-labelledby="example-risks">
      <div className="p-5"><h2 id="example-risks" className="text-lg font-semibold">Example risk register</h2><p className="muted mt-1 text-sm">Fictional LedgerPeak Payments records. Scores are likelihood × impact.</p></div>
      <div className="overflow-x-auto"><table className="risk-table"><caption className="sr-only">Fictional risk priorities, owners, and next actions</caption><thead><tr><th scope="col">Risk</th><th scope="col">Priority</th><th scope="col">Owner</th><th scope="col">Status</th><th scope="col">Next action</th></tr></thead><tbody>{demoRisks.map((risk) => <tr key={risk.title}><td><p className="font-medium">{risk.title}</p><p className="muted mt-1 text-xs">{risk.controls.join(", ")}</p></td><td><span className={risk.likelihood * risk.impact >= 15 ? "status-danger" : risk.likelihood * risk.impact >= 8 ? "status-warning" : "status-success"}>{risk.likelihood * risk.impact >= 15 ? "High" : risk.likelihood * risk.impact >= 8 ? "Medium" : "Low"} · {risk.likelihood * risk.impact}</span></td><td>{risk.owner}</td><td>{risk.status}</td><td>{risk.next}</td></tr>)}</tbody></table></div>
    </section>
    <details className="surface mb-6 p-5" id="risk-heatmap"><summary className="text-link cursor-pointer">View example risk heatmap</summary><p className="muted mt-3 text-sm">Likelihood runs from 5 (top) to 1 (bottom); impact runs from 1 to 5 left to right.</p><div className="mt-5 grid max-w-3xl grid-cols-5 gap-2" aria-label="Example risk heatmap">{[5,4,3,2,1].flatMap((likelihood) => [1,2,3,4,5].map((impact) => <div key={likelihood + "-" + impact} className={`border border-[var(--line)] p-3 ${likelihood * impact >= 15 ? "status-danger" : likelihood * impact >= 8 ? "status-warning" : "status-success"}`} aria-label={`Likelihood ${likelihood}, impact ${impact}, score ${likelihood * impact}`}><span className="font-semibold">{likelihood * impact}</span><span className="mt-2 block whitespace-normal text-xs">{demoRisks.filter((risk) => risk.likelihood === likelihood && risk.impact === impact).length} risks</span></div>))}</div></details>
  </>}><LiveRiskRegister /></ToolPage>;
}
