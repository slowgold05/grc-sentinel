"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { AuthControls } from "./auth-controls";

const navigation = [
  ["/", "Overview", "OV"],
  ["/ai-systems", "AI systems", "AI"],
  ["/risks", "Risk register", "RK"],
  ["/monitoring", "Monitoring", "MN"],
  ["/policies", "Policies", "PL"],
  ["/questionnaires", "Questionnaires", "QA"],
  ["/framework-drift", "Frameworks", "FW"],
  ["/trust", "Trust center", "TC"],
] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  if (pathname.startsWith("/sign-") || pathname.startsWith("/audit/share/")) return children;

  return (
    <div className="app-shell min-h-screen bg-[#f5f7f9] text-slate-950 lg:grid lg:grid-cols-[248px_minmax(0,1fr)]">
      <aside className="border-b border-slate-200 bg-white lg:sticky lg:top-0 lg:h-screen lg:border-b-0 lg:border-r">
        <div className="flex h-16 items-center justify-between px-5 lg:h-auto lg:px-6 lg:py-7">
          <Link href="/" className="flex items-center gap-3 font-semibold tracking-tight">
            <span className="grid size-9 place-items-center rounded-xl bg-[#5b45e0] text-sm font-bold text-white">GS</span>
            <span>GRC Sentinel</span>
          </Link>
          <details className="relative lg:hidden">
            <summary className="cursor-pointer list-none rounded-lg border border-slate-200 px-3 py-2 text-sm">Menu</summary>
            <nav className="absolute right-0 z-30 mt-2 w-56 rounded-xl border border-slate-200 bg-white p-2 shadow-xl">
              {navigation.map(([href, label]) => <Link key={href} href={href} className="block rounded-lg px-3 py-2 text-sm hover:bg-slate-100">{label}</Link>)}
            </nav>
          </details>
        </div>
        <nav className="hidden px-3 lg:block" aria-label="Primary navigation">
          <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">Workspace</p>
          {navigation.map(([href, label, icon]) => {
            const active = href === "/" ? pathname === href : pathname.startsWith(href);
            return <Link key={href} href={href} className={`mb-1 flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium ${active ? "bg-violet-50 text-[#5138d4]" : "text-slate-600 hover:bg-slate-50 hover:text-slate-950"}`}><span className="w-5 text-center text-[10px] font-bold tracking-tight text-slate-400" aria-hidden>{icon}</span>{label}</Link>;
          })}
        </nav>
        <div className="absolute bottom-0 hidden w-[247px] border-t border-slate-200 bg-white p-4 lg:block"><AuthControls /></div>
      </aside>
      <div className="min-w-0">{children}</div>
    </div>
  );
}
