import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { AppShell } from "../components/app-shell";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL ?? "https://sentinel-grc-ai.vercel.app"),
  title: "Sentinel GRC",
  description: "Evidence-grounded GRC automation and continuous compliance",
  icons: { icon: "/brand/mark.png", apple: "/brand/mark.png" },
  openGraph: { title: "Sentinel GRC", images: [{ url: "/brand/full-logo.png", width: 1448, height: 1086, alt: "Sentinel GRC logo" }] },
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
