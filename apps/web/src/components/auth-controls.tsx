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
    return <span className="rounded-full border border-zinc-700 px-4 py-2 text-slate-400">Demo mode</span>;
  }
  return (
    <>
      <Show when="signed-out">
        <SignInButton>
          <button className="rounded-full border border-red-500/30 px-4 py-2 font-medium text-red-400 hover:bg-red-500/10">Sign in</button>
        </SignInButton>
        <SignUpButton>
          <button className="rounded-full bg-red-400 px-4 py-2 font-semibold text-slate-950 hover:bg-red-300">Sign up</button>
        </SignUpButton>
      </Show>
      <Show when="signed-in"><OrganizationSwitcher hidePersonal /><UserButton /></Show>
    </>
  );
}
