import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { AppShell } from "../components/app-shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sentinal",
  description: "Evidence-grounded GRC automation and continuous compliance",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        {process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
          ? <ClerkProvider><AppShell>{children}</AppShell></ClerkProvider>
          : <AppShell>{children}</AppShell>}
      </body>
    </html>
  );
}
