import { FrameworkImpact } from "../../components/framework-impact";
import { ToolPage } from "../../components/tool-page";

/** Compare installed versions and review the policies affected by changes. */
export default function FrameworkDriftPage() {
  return <ToolPage title="Framework changes" description="Compare two installed versions of a framework and find policy statements that need another review."><FrameworkImpact /></ToolPage>;
}
