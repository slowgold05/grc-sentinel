import Image from "next/image";
import Link from "next/link";
import { ProductPreview } from "../components/product-preview";
import assessmentImage from "../../public/product/assessment.png";
import aiImage from "../../public/product/ai-system.png";
import policyImage from "../../public/product/policy.png";

const regimes = ["GLBA", "PCI DSS", "Regulation S-P", "FINRA 4370", "NYDFS 500", "SOX 404", "CCPA / CPRA", "DORA", "MAS TRM", "HIPAA", "ISO 27001", "SOC 2", "NIST 800-53", "NIST AI RMF", "ISO 42001"];
const features = [
  { id: "compliance", label: "Compliance", eyebrow: "CONNECT THE REQUIREMENT TO THE PROOF", title: "Know what is documented. See what is missing.", description: "Bring your company profile and policies into one workspace. Review requirements, inspect the supporting text, and turn gaps into a clear next action.", image: assessmentImage, tone: "assessment", alt: "Sentinal public assessment showing example policy excerpts and covered, partial, or missing checks", href: "/demo#assessment", action: "Explore the assessment" },
  { id: "ai-governance", label: "AI governance", eyebrow: "KEEP PEOPLE IN THE DECISION", title: "Govern the AI you use. Not just the policies you write.", description: "Record each system's purpose, data, owner, and human oversight. Keep risk assessments, evaluations, and approval decisions connected to the system they govern.", image: aiImage, tone: "ai-system", alt: "Sentinal fictional support-assistant record with an owner, purpose, hosting details, and human oversight", href: "/demo#ai-system", action: "Meet the example AI system" },
  { id: "evidence", label: "Policy & evidence", eyebrow: "MAKE THE REVIEW EASIER", title: "Less searching for evidence. More clarity for the reviewer.", description: "Keep policy statements connected to their sources and review decisions. Share approved work through scoped, expiring Audit Hub links when it is ready.", image: policyImage, tone: "policy", alt: "Sentinal illustrative policy extract clearly labelled as requiring human review", href: "/demo#policy", action: "Inspect a policy example" },
];
const steps = [
  ["Describe", "Add the company profile and scope facts."],
  ["Connect", "Upload policies and find supporting evidence."],
  ["Review", "Resolve gaps and record human decisions."],
  ["Share", "Export reviewed work or create an expiring audit link."],
];

/** Screenshot-led public introduction; no tenant records are requested or modified. */
export default function Home() {
  return <main className="landing-page">
    <section className="landing-hero" aria-labelledby="platform-heading">
      <div className="hero-orbit" aria-hidden="true"><div className="orbit-globe" /><div className="orbit-grid" /><div className="orbit-satellite" /></div>
      <div className="marketing-container hero-layout">
        <div className="hero-copy"><p className="hero-eyebrow">EVIDENCE. OVERSIGHT. TRUST.</p><h1 id="platform-heading">Compliance, with the evidence to back it.</h1><p className="hero-muted">Understand your requirements, find policy gaps, and keep human oversight of your AI. One workspace. A clearer picture.</p><div className="hero-actions"><Link className="primary-button" href="/demo">Explore demo <span aria-hidden>→</span></Link><Link className="hero-link" href="/workspace">Open workspace →</Link></div><p className="hero-note">Fictional data. Real workflows. No account needed to explore.</p></div>
        <div className="hero-product"><ProductPreview /></div>
      </div>
      <div className="marketing-container framework-strip" id="frameworks"><p className="hero-muted">REGULATIONS & FRAMEWORKS REPRESENTED <span>Coverage varies · Not certifications</span></p><details className="ticker-control"><summary>Pause framework strip</summary><span className="sr-only">Close to resume.</span></details><div className="framework-marquee" aria-label="Regulations and frameworks represented"><div className="framework-marquee__track">{[0, 1].map((copy) => <div key={copy} className="framework-marquee__group" aria-hidden={copy === 1}>{regimes.map((regime) => <span key={regime}>{regime}</span>)}</div>)}</div></div></div>
    </section>
    <section className="product-showcase" id="platform" aria-labelledby="showcase-heading">
      <div className="marketing-container showcase-frame"><header className="section-intro"><p className="hero-eyebrow">THE SENTINAL PLATFORM</p><h2 id="showcase-heading">Your requirements. Your AI.<br />The evidence that connects them.</h2><p>See how the work fits together, before you create an account.</p></header>
        <nav className="product-jump-nav" aria-label="Platform capabilities">{features.map((feature, index) => <a key={feature.id} href={"#" + feature.id}><span>0{index + 1}</span>{feature.label}<span aria-hidden>↓</span></a>)}</nav>
        {features.map((feature, index) => <article key={feature.id} id={feature.id} className={"feature-row" + (index % 2 ? " feature-reverse" : "")}><div className="feature-copy"><p className="hero-eyebrow">{feature.eyebrow}</p><h3>{feature.title}</h3><p>{feature.description}</p><Link className="hero-link" href={feature.href}>{feature.action} →</Link><span className="feature-note">Explore fictional example records</span></div><figure className={"feature-image feature-image-" + feature.tone}><Link href={feature.href} aria-label={feature.action}><Image src={feature.image} alt={feature.alt} sizes="(max-width: 760px) 90vw, 600px" /></Link><figcaption>CAPTURED FROM SENTINAL · PUBLIC DEMO</figcaption></figure></article>)}
      </div>
    </section>
    <section className="workflow-section" id="how-it-works"><div className="marketing-container"><div className="workflow-heading"><p className="eyebrow">FROM COMPLEXITY TO A CLEAR NEXT STEP</p><h2>You don’t need to start<br />with every answer.</h2><p className="muted">Start with what you know. Sentinal organizes the questions, evidence, and reviews that come next.</p></div><ol className="workflow-steps">{steps.map(([title, description], index) => <li key={title}><span>0{index + 1}</span><h3>{title}</h3><p className="muted">{description}</p></li>)}</ol></div></section>
    <section className="closing-section"><div className="marketing-container closing-layout"><div><p className="hero-eyebrow">BUILT FOR A HUMAN DECISION</p><h2>AI can draft.<br />People decide.</h2><p>Sentinal checks generated references and keeps approval with a person. Explore the safeguards behind the platform.</p><Link className="hero-link" href="/trust">Inside the trust center →</Link></div><div className="closing-cta"><p>TAKE A CLOSER LOOK</p><h3>See the work.<br />Follow the evidence.</h3><Link className="primary-button" href="/demo">Explore Sentinal <span aria-hidden>→</span></Link></div></div></section>
    <footer className="marketing-footer"><div className="marketing-container"><div className="footer-top"><Link href="/" className="brand">SENTINAL</Link><nav aria-label="Footer navigation"><Link href="/demo">Demo</Link><Link href="/workspace">Workspace</Link><Link href="/trust">Trust center</Link></nav></div><p><strong>Portfolio prototype.</strong> Examples are fictional. Not legal advice, certification, or an audit opinion. Candidate rules and generated policies require qualified human review before real-world use.</p></div></footer>
  </main>;
}
