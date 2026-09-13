/** Fictional examples for the public tour; never tenant records or legal findings. */
export const demoChecks = [
  { title: "Account access", status: "Covered", quote: "Payment-platform access is reviewed quarterly by the system owner.", next: "Keep the next access review with the policy." },
  { title: "Multi-factor authentication", status: "Covered", quote: "Multi-factor authentication is required for every privileged payment-system account.", next: "Keep current configuration evidence." },
  { title: "Event logging", status: "Partial", quote: "Authentication and payment-administration events are retained for 30 days.", next: "Define alerting ownership and the approved retention period." },
  { title: "Stored data protection", status: "Covered", quote: "Stored payment data uses envelope encryption with tenant-bound keys.", next: "Keep the encryption configuration review." },
  { title: "Incident response", status: "Missing", quote: "", next: "Assign an owner to document and test the incident procedure." },
  { title: "Data retention", status: "Partial", quote: "Payment records expire according to a documented retention schedule.", next: "Document legal holds and deletion evidence." },
] as const;

export const demoCovered = demoChecks.filter((check) => check.status === "Covered").length;
export const demoPartial = demoChecks.filter((check) => check.status === "Partial").length;
export const demoMissing = demoChecks.filter((check) => check.status === "Missing").length;

export const demoRisks = [
  { title: "Administrator credential compromise", likelihood: 3, impact: 5, controls: ["IA-2"], status: "Mitigating", owner: "Security", next: "Review privileged accounts and MFA evidence." },
  { title: "Delayed payment incident escalation", likelihood: 3, impact: 4, controls: ["IR-4"], status: "Open", owner: "Operations", next: "Assign an incident lead and test the escalation procedure." },
  { title: "Excessive payment-data retention", likelihood: 2, impact: 3, controls: ["SI-12"], status: "Accepted", owner: "Data operations", next: "Review the retention exception and deletion evidence." },
] as const;
