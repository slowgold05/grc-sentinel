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
      <header className="sticky top-0 z-40 border-b border-slate-700 bg-[#111e27] text-white">
        <div className="mx-auto flex h-16 max-w-[1600px] items-center gap-3 px-4 sm:px-6">
          <Link href="/" className="flex items-center gap-3 font-bold tracking-wide">
            <span className="grid size-9 place-items-center bg-[#4f7cff] text-sm font-bold text-white">S</span>
            <span className="whitespace-nowrap text-lg">SENTINAL</span>
          </Link>
          <nav className="hidden min-w-0 flex-1 items-center justify-center overflow-x-auto md:flex" aria-label="Primary navigation">
            {navigation.map(([href, label]) => {
              const active = href === "/" ? pathname === href : pathname.startsWith(href);
              return <Link key={href} href={href} className={`whitespace-nowrap border-b-2 px-2 py-5 text-xs font-medium lg:px-3 lg:text-sm ${active ? "border-[#4f7cff] text-white" : "border-transparent text-slate-300 hover:text-white"}`}>{label}</Link>;
            })}
          </nav>
          <div className="ml-auto flex items-center gap-2">
            <div className="hidden items-center gap-2 xl:flex"><AuthControls /></div>
            <details className="relative md:hidden">
            <summary className="cursor-pointer list-none border border-slate-500 px-3 py-2 text-sm">Menu</summary>
            <nav className="absolute right-0 z-30 mt-2 w-56 border border-slate-200 bg-white p-2 text-slate-950 shadow-xl">
              {navigation.map(([href, label]) => <Link key={href} href={href} className="block px-3 py-2 text-sm hover:bg-slate-100">{label}</Link>)}
              <div className="mt-2 border-t border-slate-200 p-2"><AuthControls /></div>
            </nav>
            </details>
          </div>
        </div>
        <div className="border-t border-white/10"><div className="mx-auto flex h-8 max-w-[1600px] items-center justify-end px-4 sm:px-6"><button type="button" onClick={toggleTheme} className="px-2 text-base text-slate-300 hover:text-white" aria-label={`Use ${dark ? "light" : "dark"} theme`} title={`Use ${dark ? "light" : "dark"} theme`}>{dark ? "☀" : "☾"}</button></div></div>
      </header>
      <div>{children}</div>
    </div>
  );
}
