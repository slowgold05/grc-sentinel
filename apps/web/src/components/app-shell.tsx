"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
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
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("grc-theme") === "dark";
    setDark(saved);
    document.documentElement.dataset.theme = saved ? "dark" : "light";
  }, []);

  function toggleTheme() {
    const next = !dark;
    setDark(next);
    document.documentElement.dataset.theme = next ? "dark" : "light";
    localStorage.setItem("grc-theme", next ? "dark" : "light");
  }

  if (pathname.startsWith("/sign-") || pathname.startsWith("/audit/share/")) return children;

  return (
    <div className="app-shell min-h-screen bg-[#f5f7f9] text-slate-950">
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-[1600px] items-center gap-5 px-5 sm:px-8">
          <Link href="/" className="flex items-center gap-3 font-semibold tracking-tight">
            <span className="grid size-9 place-items-center rounded-xl bg-[#5b45e0] text-sm font-bold text-white">GS</span>
            <span className="whitespace-nowrap">GRC Sentinel</span>
          </Link>
          <nav className="hidden min-w-0 flex-1 items-center gap-1 overflow-x-auto xl:flex" aria-label="Primary navigation">
            {navigation.map(([href, label]) => {
              const active = href === "/" ? pathname === href : pathname.startsWith(href);
              return <Link key={href} href={href} className={`whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium ${active ? "bg-violet-50 text-[#5138d4]" : "text-slate-600 hover:bg-slate-50 hover:text-slate-950"}`}>{label}</Link>;
            })}
          </nav>
          <div className="ml-auto flex items-center gap-2">
            <button type="button" onClick={toggleTheme} className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600" aria-label={`Use ${dark ? "light" : "dark"} theme`}>{dark ? "Light" : "Dark"}</button>
            <div className="hidden items-center gap-2 xl:flex"><AuthControls /></div>
            <details className="relative xl:hidden">
            <summary className="cursor-pointer list-none rounded-lg border border-slate-200 px-3 py-2 text-sm">Menu</summary>
            <nav className="absolute right-0 z-30 mt-2 w-56 rounded-xl border border-slate-200 bg-white p-2 shadow-xl">
              {navigation.map(([href, label]) => <Link key={href} href={href} className="block rounded-lg px-3 py-2 text-sm hover:bg-slate-100">{label}</Link>)}
              <div className="mt-2 border-t border-slate-200 p-2"><AuthControls /></div>
            </nav>
            </details>
          </div>
        </div>
      </header>
      <div>{children}</div>
    </div>
  );
}
