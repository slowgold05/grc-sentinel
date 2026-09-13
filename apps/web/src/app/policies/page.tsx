import Link from "next/link";
import { PolicyLibrary } from "../../components/policy-library";
import { ToolPage } from "../../components/tool-page";

/** Policy exports with a public example of the review workflow. */
export default function PoliciesPage() {
  return <ToolPage title="Policies" description="Review drafts and download policies with their source references." example={<section className="surface p-6"><p className="eyebrow">Illustrative policy</p><h2 className="mt-2 text-xl font-semibold">Payment-platform access</h2><p className="muted mt-2 text-sm leading-6">See how policy wording connects to a document check and its next action.</p><Link className="text-link mt-4 inline-block" href="/demo#policy">Read the policy example →</Link></section>}><PolicyLibrary /></ToolPage>;
}
