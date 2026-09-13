import { LiveMonitoring } from "../../components/live-monitoring";
import { ToolPage } from "../../components/tool-page";

/** Read-only connector workspace. */
export default function MonitoringPage() {
  return <ToolPage title="Monitoring" description="Connect GitHub or AWS with read-only access to collect evidence and see changes in safeguards."><LiveMonitoring /></ToolPage>;
}
