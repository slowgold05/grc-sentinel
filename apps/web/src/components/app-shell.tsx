"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { AuthControls } from "./auth-controls";

const navigation = [
  ["/", "Home"], ["/demo", "Demo"], ["/workspace", "Workspace"],
  ["/ai-systems", "AI systems"], ["/risks", "Risks"], ["/monitoring", "Monitoring"],
  ["/policies", "Policies"], ["/questionnaires", "Questionnaires"],
  ["/framework-drift", "Frameworks"], ["/trust", "Trust center"],
] as const;

/** Responsive navigation with account access and a persistent, optional theme preference. */
export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [dark, setDark] = useState(false);
  const publicPage = pathname === "/" || pathname === "/demo" || pathname === "/trust";

  useEffect(() => {
    let saved: string | null = null;
    try { saved = localStorage.getItem("grc-theme"); } catch { /* Storage can be unavailable in private browsers. */ }
    const next = saved ? saved === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    setDark(next);
    document.documentElement.dataset.theme = next ? "dark" : "light";
  }, []);

  function toggleTheme() {
    const next = !dark;
    setDark(next);
    document.documentElement.dataset.theme = next ? "dark" : "light";
    try { localStorage.setItem("grc-theme", next ? "dark" : "light"); } catch { /* The toggle still works for this visit. */ }
  }

  if (pathname.startsWith("/sign-") || pathname.startsWith("/audit/share/")) return children;
  return <div className="app-shell">
    <a href="#main-content" className="skip-link">Skip to content</a>
    <header className="site-header">
      <div className="header-main marketing-container">
        <Link href="/" className="brand" aria-label="Sentinal home"><span aria-hidden>S</span>SENTINAL</Link>
        <nav className="site-nav" aria-label="Primary navigation">
          <details className="platform-menu" onPointerEnter={(event) => { if (event.pointerType === "mouse") event.currentTarget.open = true; }} onPointerLeave={(event) => { if (!event.currentTarget.contains(document.activeElement)) event.currentTarget.open = false; }} onBlur={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) event.currentTarget.open = false; }} onKeyDown={(event) => { if (event.key === "Escape") { event.currentTarget.open = false; event.currentTarget.querySelector("summary")?.focus(); } }}>
            <summary>Platform <span aria-hidden>⌄</span></summary>
            <div className="platform-dropdown">
              <div className="menu-intro"><p>THE SENTINAL PLATFORM</p><h2>Clarity, from policy<br />to proof.</h2><Link href="/demo" onClick={(event) => { event.currentTarget.closest("details")?.removeAttribute("open"); }}>Explore the public demo →</Link></div>
              <div className="menu-links">{navigation.filter(([href]) => href !== "/" && href !== "/demo").map(([href, label]) => <Link key={href} href={href} aria-current={pathname === href ? "page" : undefined} onClick={(event) => { event.currentTarget.closest("details")?.removeAttribute("open"); }}>{label}<span aria-hidden>→</span></Link>)}</div>
            </div>
          </details>
          <Link href="/#frameworks">Frameworks</Link><Link href="/#ai-governance">AI governance</Link><Link href="/#how-it-works">How it works</Link>
        </nav>
        <div className="account-controls"><AuthControls /></div>
      </div>
      {!publicPage && <nav className="workspace-nav marketing-container" aria-label="Workspace navigation">{navigation.filter(([href]) => href !== "/").map(([href, label]) => <Link key={href} href={href} aria-current={pathname === href ? "page" : undefined}>{label}</Link>)}</nav>}
      <div className="theme-row marketing-container"><Link href="/demo">EXPLORE THE PLATFORM <span aria-hidden>→</span></Link><button type="button" className="theme-toggle" onClick={toggleTheme} aria-label={dark ? "Use light theme" : "Use dark theme"} aria-pressed={dark} title={dark ? "Use light theme" : "Use dark theme"}>
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
          {dark ? <><circle cx="12" cy="12" r="4" /><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5" /></> : <path d="M20 14a8.5 8.5 0 0 1-10-10 8.5 8.5 0 1 0 10 10Z" />}
        </svg>
      </button></div>
    </header>
    <div id="main-content" tabIndex={-1}>{children}</div>
  </div>;
}
