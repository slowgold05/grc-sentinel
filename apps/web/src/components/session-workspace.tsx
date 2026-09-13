"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { AuthControls } from "./auth-controls";

/** Keep authentication and organization selection explicit before tenant tools render. */
export function SessionWorkspace({ children }: { children: React.ReactNode }) {
  const { isLoaded, userId, orgId } = useAuth();
  if (!isLoaded) return <p className="muted py-6" role="status">Loading your workspace…</p>;
  if (!userId || !orgId) return <section className="surface my-6 p-6">
    <h2 className="text-lg font-semibold">{userId ? "Choose your organization" : "Open your own workspace"}</h2>
    <p className="muted mt-2 max-w-xl text-sm leading-6">{userId ? "Select or create an organization to manage its assessments." : "Sign in to create assessments and save your work. The public demo is available without an account."}</p>
    <div className="mt-4 flex flex-wrap items-center gap-3"><AuthControls /><Link className="text-link" href="/demo">Explore the demo</Link></div>
  </section>;
  return children;
}
