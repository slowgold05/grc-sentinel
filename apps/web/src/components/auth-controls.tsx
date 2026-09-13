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
          <button className="secondary-button">Sign in</button>
        </SignInButton>
        <SignUpButton>
          <button className="primary-button">Sign up</button>
        </SignUpButton>
      </Show>
      <Show when="signed-in"><OrganizationSwitcher hidePersonal /><UserButton /></Show>
    </>
  );
}
