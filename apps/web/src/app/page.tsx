import Link from "next/link";
import { DemoPreview } from "../components/demo-preview";

const regimes = ["GLBA", "PCI DSS", "Regulation S-P", "FINRA 4370", "NYDFS 500", "SOX 404", "CCPA / CPRA", "DORA", "MAS TRM", "HIPAA", "ISO 27001", "SOC 2", "NIST 800-53", "NIST AI RMF", "ISO 42001"];
const steps = [
  ["Describe the company", "Answer questions about where the business operates, its customers, and the data it handles."],
  ["Review what matters", "Record regulatory scope and assurance goals, with expert review where needed."],
  ["Find the missing proof", "Compare policies with safeguards and see the supporting text for each finding."],
  ["Put the next step in motion", "Track risks, review drafts, and share organized evidence with a reviewer."],
];

/** Public introduction; assessments and company data live in the workspace. */
export default function Home() {
  return <main className="landing-page">
    <section className="landing-hero" aria-labelledby="platform-heading">
      <div className="mx-auto grid max-w-[1440px] items-center gap-10 px-5 py-12 sm:px-8 sm:py-16 lg:grid-cols-2 lg:gap-16 lg:py-20">
        <div>
          <p className="hero-eyebrow">Security, compliance & AI governance</p>
          <h1 id="platform-heading" className="mt-5 text-4xl font-semibold leading-[1.08] tracking-tight sm:text-5xl xl:text-6xl">Turn compliance work into a clear plan.</h1>
          <p className="hero-muted mt-6 max-w-xl text-lg leading-8">Sentinal helps teams organize security requirements, find gaps in their policies, and keep the proof ready for review.</p>
          <p className="hero-muted mt-3 max-w-xl text-base leading-7">From protecting payment data to reviewing AI tools, see what is documented, what needs attention, and who needs to review it.</p>
          <div className="mt-8 flex flex-wrap gap-3"><Link className="primary-button" href="/demo">Explore demo <span aria-hidden>→</span></Link><Link className="hero-secondary" href="/workspace">Open workspace</Link></div>
          <p className="hero-muted mt-4 text-sm">The product tour is read-only. No account required.</p>
        </div>
        <DemoPreview />
      </div>
      <div className="border-t border-white/20 py-5">
        <p className="hero-muted mb-4 px-5 text-center text-xs uppercase leading-5 tracking-widest">Regulations & frameworks represented · Coverage varies</p>
        <details className="ticker-control">
          <summary>Pause framework strip</summary>
          <div className="sr-only">Animation paused. Close this control to resume.</div>
        </details>
        <div className="framework-marquee" aria-label="Regulations and frameworks represented">
          <div className="framework-marquee__track">{[0, 1].map((copy) => <div key={copy} className="framework-marquee__group" aria-hidden={copy === 1}>{regimes.map((regime) => <span key={regime}>{regime}</span>)}</div>)}</div>
        </div>
      </div>
    </section>
    <section className="mx-auto max-w-[1440px] px-5 py-12 sm:px-8 sm:py-16" id="how-it-works">
      <div className="max-w-2xl"><p className="eyebrow">What does Sentinal do?</p><h2 className="mt-3 text-3xl font-semibold tracking-tight">Bring the work and its evidence together.</h2><p className="muted mt-4 text-base leading-7">Compliance means showing that your company follows the requirements it is responsible for. Sentinal gives business, security, and audit teams a shared place to organize that work.</p></div>
      <ol className="mt-8 grid gap-0 border border-[var(--line)] md:grid-cols-2 xl:grid-cols-4">{steps.map(([title, description], index) => <li key={title} className="surface border-0 p-6"><span className="eyebrow">0{index + 1}</span><h3 className="mt-4 text-lg font-semibold">{title}</h3><p className="muted mt-3 text-sm leading-6">{description}</p></li>)}</ol>
    </section>
    <section className="mx-auto grid max-w-[1440px] gap-8 border-t border-[var(--line)] px-5 py-12 sm:px-8 lg:grid-cols-2">
      <div><p className="eyebrow">AI needs oversight too</p><h2 className="mt-3 text-3xl font-semibold tracking-tight">Know how your team uses AI.</h2><p className="muted mt-4 max-w-xl leading-7">Record what an AI tool does, what information it uses, and who reviews its output. Keep assessments and approval decisions alongside the system record.</p><Link className="text-link mt-6 inline-block" href="/demo#ai-system">Meet the example support assistant →</Link></div>
      <div className="surface p-6 sm:p-8"><p className="eyebrow">Built for a human decision</p><h3 className="mt-3 text-xl font-semibold">AI drafts. People review.</h3><p className="muted mt-4 leading-7">The model helps draft policies using retrieved sources. The application checks cited control references, while a person reviews the result before use.</p><Link className="text-link mt-6 inline-block" href="/demo#policy">Read an illustrative policy extract →</Link></div>
    </section>
    <footer className="border-t border-[var(--line)] px-5 py-8 sm:px-8"><div className="mx-auto flex max-w-[1376px] flex-wrap items-start justify-between gap-6"><p className="muted max-w-3xl text-sm leading-6"><strong>Portfolio prototype.</strong> The demo uses fictional records. Sentinal is not legal advice, certification, or an audit opinion. Candidate rules and generated policies require qualified review before real-world use.</p><Link className="text-link text-sm" href="/trust">Platform safeguards →</Link></div></footer>
  </main>;
}
