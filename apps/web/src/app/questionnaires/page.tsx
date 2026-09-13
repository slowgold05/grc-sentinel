import { QuestionnaireReview } from "../../components/questionnaire-review";
import { ToolPage } from "../../components/tool-page";

/** Human review of answers supported by existing policy statements. */
export default function QuestionnairesPage() {
  return <ToolPage title="Questionnaires" description="Review suggested answers, check their policy references, and approve or reject each response."><QuestionnaireReview /></ToolPage>;
}
