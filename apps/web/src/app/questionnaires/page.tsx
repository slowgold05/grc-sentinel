import Link from "next/link";
import { QuestionnaireReview } from "../../components/questionnaire-review";

export default function QuestionnairesPage() {
  return <main className="min-h-screen bg-black px-5 py-10 text-slate-100 sm:px-8"><div className="mx-auto max-w-[1600px]"><Link href="/" className="text-sm text-red-400">← Coverage</Link><p className="mt-8 text-xs font-semibold uppercase tracking-[0.24em] text-red-500">Human review</p><h1 className="mt-3 text-4xl font-semibold">Security questionnaire answers</h1><p className="mt-4 max-w-2xl text-slate-400">Approve, edit, or reject answers grounded in verified policy statements.</p>{process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ? <QuestionnaireReview /> : <p className="mt-8 text-amber-200">Configure Clerk to use live review.</p>}</div></main>;
}
