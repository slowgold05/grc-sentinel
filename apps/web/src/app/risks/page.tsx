import Link from "next/link";
import { LiveRiskRegister } from "../../components/live-risk-register";

const risks = [
  { title: "Administrator credential compromise", likelihood: 3, impact: 5, controls: ["IA-2"], status: "Mitigating" },
  { title: "Delayed payment incident escalation", likelihood: 3, impact: 4, controls: ["IR-4"], status: "Open" },
  { title: "Excessive payment-data retention", likelihood: 2, impact: 3, controls: ["SI-12"], status: "Accepted" },
] as const;

const likelihoods = [5, 4, 3, 2, 1];
const impacts = [1, 2, 3, 4, 5];

function severity(score: number) {
  if (score >= 15) return "border-rose-400/40 bg-rose-400/15 text-rose-100";
  if (score >= 8) return "border-amber-400/40 bg-amber-400/15 text-amber-100";
  return "border-emerald-400/30 bg-emerald-400/10 text-emerald-100";
}

export default function RisksPage() {
  return (
    <main className="min-h-screen bg-black px-5 py-10 text-slate-100 sm:px-8 lg:py-16">
      <div className="mx-auto max-w-[1600px]">
        <Link href="/" className="text-sm font-medium text-red-400 hover:text-red-300">&larr; Coverage demo</Link>
        <header className="mt-8 border-b border-zinc-800 pb-8">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-red-500">LedgerPeak Payments / Risk register</p>
          <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">Risk, linked to controls.</h1>
          <p className="mt-4 max-w-2xl leading-7 text-slate-400">Scores are likelihood × impact. Select a populated cell to review the treatment and mapped controls.</p>
        </header>

        {process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY && <LiveRiskRegister />}

        <section className="grid gap-10 py-10 lg:grid-cols-[1fr_22rem]">
          <div>
            <div className="mb-2 grid grid-cols-[2.5rem_repeat(5,minmax(0,1fr))] gap-2 text-center text-xs text-slate-500">
              <span />{impacts.map((impact) => <span key={impact}>Impact {impact}</span>)}
            </div>
            <div className="space-y-2">
              {likelihoods.map((likelihood) => (
                <div key={likelihood} className="grid grid-cols-[2.5rem_repeat(5,minmax(0,1fr))] gap-2">
                  <span className="flex items-center text-xs text-slate-500">L{likelihood}</span>
                  {impacts.map((impact) => {
                    const matches = risks.filter((risk) => risk.likelihood === likelihood && risk.impact === impact);
                    const score = likelihood * impact;
                    return <div key={impact} aria-label={`Likelihood ${likelihood}, impact ${impact}, score ${score}`} className={`min-h-24 rounded-xl border p-3 ${severity(score)}`}><span className="text-lg font-semibold">{score}</span>{matches.map((risk) => <p key={risk.title} className="mt-2 text-xs leading-4">{risk.title}</p>)}</div>;
                  })}
                </div>
              ))}
            </div>
          </div>

          <aside aria-label="Risk details" className="space-y-3">
            {risks.map((risk) => <article key={risk.title} className="rounded-2xl border border-zinc-800 bg-zinc-950 p-5"><div className="flex items-start justify-between gap-3"><h2 className="font-semibold">{risk.title}</h2><span className="rounded-full bg-slate-800 px-2.5 py-1 text-xs text-slate-300">{risk.status}</span></div><p className="mt-4 text-sm text-slate-400">Score {risk.likelihood * risk.impact} · {risk.controls.join(", ")}</p></article>)}
          </aside>
        </section>
        <p className="text-sm text-slate-500">Fictional demonstration data. Production records remain tenant-scoped under PostgreSQL RLS.</p>
      </div>
    </main>
  );
}
