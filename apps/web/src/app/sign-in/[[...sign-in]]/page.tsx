import { SignIn } from "@clerk/nextjs";
import Image from "next/image";
import Link from "next/link";
import logo from "../../../../public/brand/full-logo.png";

export default function SignInPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 px-4 py-8">
      <Link href="/" aria-label="Sentinel GRC home"><Image src={logo} alt="Sentinel GRC" className="auth-brand" sizes="220px" priority /></Link>
      <SignIn />
    </div>
  );
}
