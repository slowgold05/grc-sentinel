import { AISystemInventory } from "../../components/ai-system-inventory";
import { DemoAISystem } from "../../components/demo-ai-system";
import { ToolPage } from "../../components/tool-page";

/** Inventory entry with an inspectable fictional system before sign-in. */
export default function AISystemsPage() {
  return <ToolPage title="AI systems" description="Track each system's purpose, owner, data use, and review decisions." example={<DemoAISystem />}><AISystemInventory /></ToolPage>;
}
