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
          <button className="border border-white/50 px-4 py-2 font-medium text-white hover:bg-white/10">Sign in</button>
        </SignInButton>
        <SignUpButton>
          <button className="bg-[#4f7cff] px-4 py-2 font-semibold text-white hover:bg-[#3e69e8]">Sign up</button>
        </SignUpButton>
      </Show>
      <Show when="signed-in"><OrganizationSwitcher hidePersonal /><UserButton /></Show>
    </>
  );
}
