import Link from "next/link";
import { AISystemInventory } from "../../components/ai-system-inventory";

export default function AISystemsPage() {
  return (
    <main className="min-h-screen bg-black px-5 py-10 text-slate-100 sm:px-8 lg:py-16">
      <div className="mx-auto max-w-[1600px]">
        <Link href="/" className="text-sm font-medium text-red-400 hover:text-red-300">&larr; Coverage demo</Link>
        <header className="mt-8 border-b border-zinc-800 pb-8">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-red-500">AI governance / Inventory</p>
          <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">Know every AI system you govern.</h1>
          <p className="mt-4 max-w-2xl leading-7 text-slate-400">Record ownership, purpose, data use, oversight, and lifecycle state before an AI system can enter an approval workflow.</p>
        </header>
        {process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ? <AISystemInventory /> : <p className="mt-8 text-amber-200">Configure Clerk to access the tenant AI inventory.</p>}
      </div>
    </main>
  );
}
