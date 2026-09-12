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
          <button className="rounded-full border border-violet-300 px-4 py-2 font-medium text-[#5138d4] hover:bg-violet-50">Sign in</button>
        </SignInButton>
        <SignUpButton>
          <button className="rounded-full bg-[#5b45e0] px-4 py-2 font-semibold text-white hover:bg-[#4933c7]">Sign up</button>
        </SignUpButton>
      </Show>
      <Show when="signed-in"><OrganizationSwitcher hidePersonal /><UserButton /></Show>
    </>
  );
}
