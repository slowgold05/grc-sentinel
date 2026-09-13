/** Public, fictional AI record matching the portfolio walkthrough's support-assistant scenario. */
export function DemoAISystem() {
  return <section className="surface p-5 sm:p-6" aria-labelledby="demo-ai-heading">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><p className="eyebrow">Fictional AI system</p><h2 id="demo-ai-heading" className="mt-2 text-xl font-semibold">LedgerPeak Support Assistant</h2></div><span className="status-warning">Review pending</span></div>
    <p className="muted mt-3 text-sm leading-6">Drafts customer-support replies. A support agent decides whether to send each answer.</p>
    <dl className="facts mt-5">
      {[ ["Owner", "Customer Operations"], ["Purpose", "Draft support replies for human review"], ["Data", "Support tickets"], ["Hosting", "Ollama on a local workstation"], ["External actions", "None — drafting only"], ["Oversight", "A person reviews every output"] ].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}
    </dl>
    <details className="mt-5 border-t border-[var(--line)] pt-4"><summary className="text-link cursor-pointer">Inspect the example assessment</summary><div className="mt-4 space-y-3 text-sm leading-6"><p><strong>Risk to review:</strong> an incorrect draft could mislead a customer if it is sent without checking.</p><p><strong>Review focus:</strong> confirm human oversight, document permitted data use, and evaluate sample replies.</p><p><strong>Decision:</strong> approval pending. This example does not assert a legal risk classification or a passed evaluation.</p></div></details>
  </section>;
}
