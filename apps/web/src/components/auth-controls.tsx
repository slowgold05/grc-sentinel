"use client";

import {
  OrganizationSwitcher,
  Show,
  SignInButton,
  SignUpButton,
  UserButton,
} from "@clerk/nextjs";

export function AuthControls() {
  if (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY) {
    return <span className="rounded-full border border-slate-700 px-4 py-2 text-slate-400">Demo mode</span>;
  }
  return (
    <>
      <Show when="signed-out">
        <SignInButton>
          <button className="rounded-full border border-cyan-400/30 px-4 py-2 font-medium text-cyan-300 hover:bg-cyan-400/10">Sign in</button>
        </SignInButton>
        <SignUpButton>
          <button className="rounded-full bg-cyan-300 px-4 py-2 font-semibold text-slate-950 hover:bg-cyan-200">Sign up</button>
        </SignUpButton>
      </Show>
      <Show when="signed-in"><OrganizationSwitcher hidePersonal /><UserButton /></Show>
    </>
  );
}
