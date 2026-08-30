import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

export const metadata: Metadata = { title: "Ruleset", description: "AI GRC policy platform" };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const document = <html lang="en"><body>{children}</body></html>;
  return process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
    ? <ClerkProvider>{document}</ClerkProvider>
    : document;
}
