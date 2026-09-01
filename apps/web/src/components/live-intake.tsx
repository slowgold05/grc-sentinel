"use client";

import { useAuth } from "@clerk/nextjs";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { CoverageMatrix, type CoverageRow } from "./coverage-matrix";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function optionalBoolean(value: FormDataEntryValue | null) {
  return value === "yes" ? true : value === "no" ? false : null;
}

type Engagement = {
  id: string;
  company: { company_name: string; domain: string };
  regulations: string[];
  assurance_objectives: { framework: string; version: string; basis: string }[];
  expires_at: string;
};
type Readiness = { framework: string; version: string; total: number; covered: number; partial: number; missing: number; not_assessed: number };

export function LiveIntake() {
  const { getToken, userId } = useAuth();
  const [result, setResult] = useState("");
  const [error, setError] = useState("");
  const [engagements, setEngagements] = useState<Engagement[]>([]);
  const [coverage, setCoverage] = useState<CoverageRow[] | null>(null);
  const [auditShare, setAuditShare] = useState<{ url: string; token: string } | null>(null);
  const [readiness, setReadiness] = useState<Readiness[]>([]);

  const refresh = useCallback(async () => {
    const token = await getToken();
    if (!token) return;
    const response = await fetch(`${apiUrl}/api/engagements`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error("Could not load engagements");
    setEngagements(await response.json());
  }, [getToken]);

  useEffect(() => {
    if (userId) refresh().catch((reason: Error) => setError(reason.message));
  }, [refresh, userId]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const form = new FormData(event.currentTarget);
    const token = await getToken();
    if (!token) return setError("Sign in and select an organization first");
    const pciStores = optionalBoolean(form.get("pci_stores_account_data"));
    const pciProcesses = optionalBoolean(form.get("pci_processes_account_data"));
    const pciTransmits = optionalBoolean(form.get("pci_transmits_account_data"));
    try {
      const response = await fetch(`${apiUrl}/api/engagements`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          company: {
            company_name: form.get("company_name"),
            domain: form.get("domain"),
            employee_count: Number(form.get("employee_count")),
            geos: form.get("us") ? ["us"] : [],
            data_types: [pciStores, pciProcesses, pciTransmits].includes(true) ? ["payment"] : [],
            sends_external_email: form.get("email") === "on",
            financial_services: form.get("financial_services") === "on",
            ftc_financial_institution: optionalBoolean(form.get("ftc_financial_institution")),
            handles_customer_financial_information: optionalBoolean(form.get("customer_financial_information")),
            glba_section_505_other_regulator: optionalBoolean(form.get("glba_other_regulator")),
            glba_customer_count: form.get("glba_customer_count") ? Number(form.get("glba_customer_count")) : null,
            glba_financial_activity: form.get("glba_financial_activity") || null,
            handles_cardholder_data: [pciStores, pciProcesses, pciTransmits].includes(true),
            pci_entity_role: form.get("pci_entity_role") || null,
            pci_stores_account_data: pciStores,
            pci_processes_account_data: pciProcesses,
            pci_transmits_account_data: pciTransmits,
            pci_can_impact_cde: optionalBoolean(form.get("pci_can_impact_cde")),
            pci_fully_outsourced: optionalBoolean(form.get("pci_fully_outsourced")),
            pci_cde_scope_confirmed: optionalBoolean(form.get("pci_cde_scope_confirmed")),
            pci_validation_method: form.get("pci_validation_method") || null,
            reg_sp_covered_institution: optionalBoolean(form.get("reg_sp_covered_institution")),
            reg_sp_entity_type: form.get("reg_sp_entity_type") || null,
            reg_sp_size_cohort: form.get("reg_sp_size_cohort") || null,
            reg_sp_customer_information: optionalBoolean(form.get("reg_sp_customer_information")),
            reg_sp_service_provider_used: optionalBoolean(form.get("reg_sp_service_provider_used")),
            finra_member: optionalBoolean(form.get("finra_member")),
            finra_firm_type: form.get("finra_firm_type") || null,
            finra_customer_accounts: optionalBoolean(form.get("finra_customer_accounts")),
            finra_mission_critical_systems_identified: optionalBoolean(form.get("finra_mission_critical_systems_identified")),
            finra_bcp_scope_confirmed: optionalBoolean(form.get("finra_bcp_scope_confirmed")),
            nydfs_licensed: optionalBoolean(form.get("nydfs_licensed")),
            nydfs_authorization_type: form.get("nydfs_authorization_type") || null,
            nydfs_exemption: form.get("nydfs_exemption") || null,
            nydfs_class_a_company: optionalBoolean(form.get("nydfs_class_a_company")),
            nydfs_uses_affiliate_program: optionalBoolean(form.get("nydfs_uses_affiliate_program")),
            exchange_act_reporting_company: form.get("sox") === "on",
            eu_financial_entity: optionalBoolean(form.get("eu_financial_entity")),
            dora_entity_type: form.get("dora_entity_type") || null,
            dora_eu_operating_nexus: optionalBoolean(form.get("dora_eu_operating_nexus")),
            dora_article_2_exclusion: form.get("dora_article_2_exclusion") || null,
            dora_group_context: optionalBoolean(form.get("dora_group_context")),
            dora_ict_third_party_provider: optionalBoolean(form.get("dora_ict_third_party_provider")),
            dora_critical_ict_provider_designated: optionalBoolean(form.get("dora_critical_ict_provider_designated")),
            dora_scope_confirmed: optionalBoolean(form.get("dora_scope_confirmed")),
            ccpa_covered_business: optionalBoolean(form.get("ccpa_covered_business")),
            california_consumer_data: optionalBoolean(form.get("california_consumer_data")),
            ccpa_for_profit: optionalBoolean(form.get("ccpa_for_profit")),
            ccpa_does_business_in_california: optionalBoolean(form.get("ccpa_does_business_in_california")),
            ccpa_determines_processing_purposes: optionalBoolean(form.get("ccpa_determines_processing_purposes")),
            ccpa_threshold_year: form.get("ccpa_threshold_year") ? Number(form.get("ccpa_threshold_year")) : null,
            ccpa_gross_revenue_usd: form.get("ccpa_gross_revenue_usd") ? Number(form.get("ccpa_gross_revenue_usd")) : null,
            ccpa_consumers_or_households: form.get("ccpa_consumers_or_households") ? Number(form.get("ccpa_consumers_or_households")) : null,
            ccpa_selling_sharing_revenue_percent: form.get("ccpa_selling_sharing_revenue_percent") ? Number(form.get("ccpa_selling_sharing_revenue_percent")) : null,
            ccpa_related_entity: optionalBoolean(form.get("ccpa_related_entity")),
            ccpa_exemption: form.get("ccpa_exemption") || null,
            mas_trm_notice_subject: form.get("mas_trm") === "on",
          },
          assurance_objectives: [
            ["iso", "ISO 27001"],
            ["soc2", "SOC 2 TSC"],
            ["nist", "NIST SP 800-53"],
            ["pci", "PCI DSS"],
          ].filter(([field]) => form.get(field)).map(([, framework]) => ({
            framework,
            basis: form.get("assurance_basis"),
            target_date: form.get("target_date") || null,
            scope: form.get("assurance_scope") || "",
          })),
        }),
      });
      if (!response.ok) return setError("Could not create engagement");
      const payload = await response.json();
      const regulations = payload.determinations.map((item: { regulation: string }) => item.regulation);
      const objectives = payload.assurance_objectives.map((item: { framework: string }) => item.framework);
      setResult([...regulations.map((item: string) => `${item} applies`), ...objectives.map((item: string) => `${item} selected`)].join(" · ") || "No current rule or assurance objective matched");
      await refresh();
    } catch {
      setError("Could not reach the intake API");
    }
  }

  async function remove(id: string) {
    const token = await getToken();
    if (!token) return;
    try {
      const response = await fetch(`${apiUrl}/api/engagements/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) return setError("Could not delete engagement");
      await refresh();
    } catch {
      setError("Could not reach the intake API");
    }
  }

  async function upload(engagementId: string, file: File) {
    const token = await getToken();
    if (!token) return;
    setError("");
    try {
      const response = await fetch(`${apiUrl}/api/engagements/${engagementId}/uploads`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/octet-stream",
          "X-Filename": file.name,
        },
        body: file,
      });
      if (!response.ok) return setError("Upload rejected; use a valid PDF or DOCX under 20 MiB");
      const payload = await response.json();
      setResult(`Indexed ${payload.embedded_sections} section(s); local AI analysis is running`);
      const analysis = await fetch(
        `${apiUrl}/api/engagements/${engagementId}/uploads/${payload.id}/analyze`,
        { method: "POST", headers: { Authorization: `Bearer ${token}` } },
      );
      if (!analysis.ok) return setError("Upload succeeded, but local AI analysis failed");
      const analyzed = await analysis.json();
      setResult(`Analyzed ${analyzed.analyzed_controls} required control(s)`);
      await inspectCoverage(engagementId);
    } catch {
      setError("Could not reach the upload API");
    }
  }

  async function inspectPosture(engagementId: string) {
    const token = await getToken();
    if (!token) return;
    setError("");
    try {
      const response = await fetch(`${apiUrl}/api/engagements/${engagementId}/posture`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) return setError("Passive posture check was unavailable");
      const payload = await response.json();
      setResult(payload.observations.join(" · "));
    } catch {
      setError("Could not reach the posture API");
    }
  }

  async function inspectCoverage(engagementId: string) {
    const token = await getToken();
    if (!token) return;
    setError("");
    try {
      const response = await fetch(`${apiUrl}/api/engagements/${engagementId}/coverage`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) return setError("Could not load coverage results");
      const rows: CoverageRow[] = await response.json();
      setCoverage(rows);
      if (!rows.length) setResult("No gap-analysis results are stored for this engagement yet");
    } catch {
      setError("Could not reach the coverage API");
    }
  }

  async function createAuditShare(engagementId: string) {
    const token = await getToken();
    if (!token) return;
    try {
      const response = await fetch(`${apiUrl}/api/engagements/${engagementId}/audit-shares`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ expires_in_hours: 24 }),
      });
      if (!response.ok) return setError("Could not create audit share");
      const payload = await response.json();
      setAuditShare({
        url: `${window.location.origin}/audit/share/${payload.token}`,
        token: payload.token,
      });
    } catch {
      setError("Could not reach the audit-share API");
    }
  }

  async function inspectReadiness(engagementId: string) {
    const token = await getToken();
    if (!token) return;
    try {
      const response = await fetch(`${apiUrl}/api/engagements/${engagementId}/assurance-readiness`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) return setError("Could not load assurance readiness");
      setReadiness(await response.json());
    } catch {
      setError("Could not reach the assurance-readiness API");
    }
  }

  async function revokeAuditShare() {
    if (!auditShare) return;
    const token = await getToken();
    if (!token) return;
    try {
      const response = await fetch(`${apiUrl}/api/audit-shares/${auditShare.token}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) return setError("Could not revoke audit share");
      setAuditShare(null);
      setResult("Audit link revoked");
    } catch {
      setError("Could not reach the audit-share API");
    }
  }

  if (!userId) return null;
  return (
    <section className="mb-10 rounded-2xl border border-red-500/20 bg-red-500/[0.04] p-6" aria-labelledby="new-engagement">
      <h2 id="new-engagement" className="text-xl font-semibold">Start a live engagement</h2>
      <p className="mt-2 text-sm text-slate-400">Capture confirmed scope facts. Only human-reviewed versioned rules create legal determinations; an LLM never does.</p>
      <form onSubmit={submit} className="mt-5 grid gap-3 sm:grid-cols-3">
        <input required name="company_name" maxLength={200} placeholder="Company name" className="rounded-lg border border-zinc-700 bg-black px-3 py-2" />
        <input required name="domain" placeholder="example.com" className="rounded-lg border border-zinc-700 bg-black px-3 py-2" />
        <input required name="employee_count" type="number" min="1" placeholder="Employees" className="rounded-lg border border-zinc-700 bg-black px-3 py-2" />
        <label className="flex items-center gap-2 text-sm"><input name="us" type="checkbox" /> Operates in the US</label>
        <label className="flex items-center gap-2 text-sm"><input name="financial_services" type="checkbox" /> Provides financial services</label>
        <label className="flex items-center gap-2 text-sm"><input name="email" type="checkbox" /> Sends external email</label>
        <fieldset className="grid gap-3 rounded-lg border border-zinc-700 p-3 sm:col-span-3"><legend className="px-2 text-sm font-semibold text-red-400">GLBA Safeguards Rule scope</legend><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3"><select name="ftc_financial_institution" defaultValue="" aria-label="FTC financial institution status" className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">FTC institution status unknown</option><option value="yes">FTC financial institution: yes</option><option value="no">FTC financial institution: no</option></select><select name="customer_financial_information" defaultValue="" aria-label="GLBA customer information status" className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">Customer information status unknown</option><option value="yes">Maintains customer information</option><option value="no">Does not maintain customer information</option></select><select name="glba_other_regulator" defaultValue="" aria-label="Other GLBA regulator status" className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">Other-regulator status unknown</option><option value="yes">Another GLBA §505 regulator enforces</option><option value="no">No other GLBA §505 regulator identified</option></select><select name="glba_financial_activity" defaultValue="" aria-label="GLBA financial activity" className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">Financial activity not selected</option><option value="mortgage_lending">Mortgage lending</option><option value="payday_lending">Payday lending</option><option value="finance_company">Finance company</option><option value="mortgage_broker">Mortgage broker</option><option value="account_servicing">Account servicing</option><option value="check_cashing">Check cashing</option><option value="wire_transfer">Wire transfer</option><option value="collection_agency">Collection agency</option><option value="credit_counseling_or_financial_advice">Credit counseling / financial advice</option><option value="tax_preparation">Tax preparation</option><option value="non_federally_insured_credit_union">Non-federally insured credit union</option><option value="non_sec_registered_investment_adviser">Non-SEC-registered investment adviser</option><option value="finder">Finder</option><option value="other_financial_activity">Other financial activity — review needed</option></select><input name="glba_customer_count" type="number" min="0" placeholder="Consumers whose information is maintained" className="rounded-lg border border-zinc-700 bg-black px-3 py-2" /></div><p className="text-xs text-slate-400">Answer from confirmed legal/entity records. Fewer than 5,000 consumers affects specified safeguards; it does not automatically remove the Rule.</p></fieldset>
        <fieldset className="grid gap-3 rounded-lg border border-zinc-700 p-3 sm:col-span-3"><legend className="px-2 text-sm font-semibold text-violet-300">PCI DSS 4.0.1 scope</legend><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><select name="pci_entity_role" defaultValue="" aria-label="PCI entity role" className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">Entity role unknown</option><option value="merchant">Merchant</option><option value="service_provider">Service provider</option><option value="merchant_and_service_provider">Merchant and service provider</option><option value="other">Other — review needed</option></select>{[["pci_stores_account_data", "Stores account data"], ["pci_processes_account_data", "Processes account data"], ["pci_transmits_account_data", "Transmits account data"], ["pci_can_impact_cde", "Can impact CDE security"], ["pci_fully_outsourced", "All payment processing outsourced"], ["pci_cde_scope_confirmed", "CDE scope confirmed"]].map(([name, label]) => <select key={name} name={name} defaultValue="" aria-label={label} className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">{label}: unknown</option><option value="yes">{label}: yes</option><option value="no">{label}: no</option></select>)}<select name="pci_validation_method" defaultValue="" aria-label="PCI validation method" className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">Validation method unknown</option><option value="saq_a">SAQ A</option><option value="saq_a_ep">SAQ A-EP</option><option value="saq_b">SAQ B</option><option value="saq_b_ip">SAQ B-IP</option><option value="saq_c">SAQ C</option><option value="saq_c_vt">SAQ C-VT</option><option value="saq_d_merchant">SAQ D — Merchant</option><option value="saq_d_service_provider">SAQ D — Service Provider</option><option value="roc">Report on Compliance</option><option value="not_determined">Not yet determined</option></select></div><p className="text-xs text-slate-400">Outsourcing can reduce directly applicable requirements but does not erase merchant oversight or validation responsibilities. Confirm the validation method with the compliance-accepting entity.</p></fieldset>
        <fieldset className="grid gap-3 rounded-lg border border-zinc-700 p-3 sm:col-span-3"><legend className="px-2 text-sm font-semibold text-red-400">SEC Regulation S-P scope</legend><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3"><select name="reg_sp_covered_institution" defaultValue="" aria-label="Regulation S-P covered institution status" className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">Covered status unknown</option><option value="yes">Covered institution: yes</option><option value="no">Covered institution: no</option></select><select name="reg_sp_entity_type" defaultValue="" aria-label="Regulation S-P entity type" className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">Entity type unknown</option><option value="broker_dealer">Broker-dealer</option><option value="investment_company">Investment company</option><option value="registered_investment_adviser">SEC-registered investment adviser</option><option value="funding_portal">Funding portal</option><option value="transfer_agent">Transfer agent</option><option value="other">Other — review needed</option></select><select name="reg_sp_size_cohort" defaultValue="" aria-label="Regulation S-P size cohort" className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">Size cohort unknown</option><option value="larger">Larger entity</option><option value="smaller">Smaller entity</option><option value="not_determined">Not determined</option></select>{[["reg_sp_customer_information", "Maintains customer information"], ["reg_sp_service_provider_used", "Uses covered service providers"]].map(([name, label]) => <select key={name} name={name} defaultValue="" aria-label={label} className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">{label}: unknown</option><option value="yes">{label}: yes</option><option value="no">{label}: no</option></select>)}</div></fieldset>
        <fieldset className="grid gap-3 rounded-lg border border-zinc-700 p-3 sm:col-span-3"><legend className="px-2 text-sm font-semibold text-red-400">FINRA Rule 4370 scope</legend><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3"><select name="finra_member" defaultValue="" aria-label="FINRA membership status" className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">Membership unknown</option><option value="yes">FINRA member: yes</option><option value="no">FINRA member: no</option></select><select name="finra_firm_type" defaultValue="" aria-label="FINRA firm type" className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">Firm type unknown</option><option value="carrying_clearing">Carrying / clearing firm</option><option value="introducing">Introducing firm</option><option value="other">Other member firm</option></select>{[["finra_customer_accounts", "Maintains customer accounts"], ["finra_mission_critical_systems_identified", "Mission-critical systems identified"], ["finra_bcp_scope_confirmed", "BCP scope confirmed"]].map(([name, label]) => <select key={name} name={name} defaultValue="" aria-label={label} className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">{label}: unknown</option><option value="yes">{label}: yes</option><option value="no">{label}: no</option></select>)}</div></fieldset>
        <fieldset className="grid gap-3 rounded-lg border border-zinc-700 p-3 sm:col-span-3"><legend className="px-2 text-sm font-semibold text-red-400">NYDFS Part 500 scope</legend><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3"><select name="nydfs_licensed" defaultValue="" aria-label="NYDFS covered entity status" className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">Covered status unknown</option><option value="yes">NYDFS covered entity: yes</option><option value="no">NYDFS covered entity: no</option></select><select name="nydfs_authorization_type" defaultValue="" aria-label="NYDFS authorization type" className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">Authorization unknown</option><option value="banking">Banking Law</option><option value="insurance">Insurance Law</option><option value="financial_services">Financial Services Law</option><option value="virtual_currency">Virtual currency authorization</option><option value="other">Other DFS authorization</option></select><select name="nydfs_exemption" defaultValue="" aria-label="NYDFS exemption" className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">Exemption unknown</option><option value="none">No exemption claimed</option><option value="500.19(a)">§500.19(a)</option><option value="500.19(b)">§500.19(b)</option><option value="500.19(c)">§500.19(c)</option><option value="500.19(d)">§500.19(d)</option><option value="500.19(e)">§500.19(e)</option><option value="not_determined">Not determined</option></select>{[["nydfs_class_a_company", "Class A company"], ["nydfs_uses_affiliate_program", "Uses affiliate cybersecurity program"]].map(([name, label]) => <select key={name} name={name} defaultValue="" aria-label={label} className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">{label}: unknown</option><option value="yes">{label}: yes</option><option value="no">{label}: no</option></select>)}</div></fieldset>
        <fieldset className="grid gap-3 rounded-lg border border-zinc-700 p-3 sm:col-span-3"><legend className="px-2 text-sm font-semibold text-red-400">CCPA / CPRA scope</legend><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{[["ccpa_covered_business", "Reviewed covered-business status"], ["california_consumer_data", "Processes California consumer PI"], ["ccpa_for_profit", "For-profit entity"], ["ccpa_does_business_in_california", "Does business in California"], ["ccpa_determines_processing_purposes", "Determines processing purposes/means"], ["ccpa_related_entity", "Covered through related-entity rules"]].map(([name, label]) => <select key={name} name={name} defaultValue="" aria-label={label} className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">{label}: unknown</option><option value="yes">{label}: yes</option><option value="no">{label}: no</option></select>)}<input name="ccpa_threshold_year" type="number" min="2020" max="2100" placeholder="Threshold year" className="rounded-lg border border-zinc-700 bg-black px-3 py-2" /><input name="ccpa_gross_revenue_usd" type="number" min="0" placeholder="Gross revenue (USD)" className="rounded-lg border border-zinc-700 bg-black px-3 py-2" /><input name="ccpa_consumers_or_households" type="number" min="0" placeholder="CA consumers / households" className="rounded-lg border border-zinc-700 bg-black px-3 py-2" /><input name="ccpa_selling_sharing_revenue_percent" type="number" min="0" max="100" step="0.01" placeholder="% revenue from selling/sharing PI" className="rounded-lg border border-zinc-700 bg-black px-3 py-2" /><select name="ccpa_exemption" defaultValue="" aria-label="CCPA exemption status" className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">Exemption unknown</option><option value="none">No exemption identified</option><option value="glba_information">GLBA-regulated information</option><option value="cfipa_information">CFIPA-regulated information</option><option value="hipaa_phi">HIPAA PHI</option><option value="nonprofit">Nonprofit entity</option><option value="government_entity">Government entity</option><option value="other">Other — review needed</option><option value="not_determined">Not determined</option></select></div><p className="text-xs text-slate-400">Thresholds are evaluated for the recorded year. Financial-data exemptions apply to qualifying information, not automatically to every record held by a financial company.</p></fieldset>
        <fieldset className="grid gap-3 rounded-lg border border-zinc-700 p-3 sm:col-span-3"><legend className="px-2 text-sm font-semibold text-red-400">DORA scope</legend><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><select name="dora_entity_type" defaultValue="" aria-label="DORA Article 2 entity category" className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">Article 2 category unknown</option><option value="credit_institution">Credit institution</option><option value="payment_institution">Payment institution</option><option value="account_information_service_provider">Account information service provider</option><option value="electronic_money_institution">Electronic money institution</option><option value="investment_firm">Investment firm</option><option value="crypto_asset_service_provider">Crypto-asset service provider</option><option value="central_securities_depository">Central securities depository</option><option value="central_counterparty">Central counterparty</option><option value="trading_venue">Trading venue</option><option value="trade_repository">Trade repository</option><option value="fund_manager">Fund manager</option><option value="data_reporting_service_provider">Data reporting service provider</option><option value="insurance_entity">Insurance / reinsurance undertaking</option><option value="insurance_intermediary">Insurance intermediary</option><option value="occupational_pension_institution">Occupational pension institution</option><option value="credit_rating_agency">Credit rating agency</option><option value="critical_benchmark_administrator">Critical benchmark administrator</option><option value="crowdfunding_service_provider">Crowdfunding service provider</option><option value="securitisation_repository">Securitisation repository</option><option value="other_article_2_entity">Other Article 2 entity</option></select><select name="dora_article_2_exclusion" defaultValue="" aria-label="DORA Article 2 exclusion" className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">Exclusion unknown</option><option value="none">No Article 2 exclusion identified</option><option value="small_alternative_investment_fund_manager">Small AIF manager</option><option value="small_insurance_or_reinsurance_undertaking">Small insurance / reinsurance undertaking</option><option value="small_occupational_pension_institution">Small occupational pension institution</option><option value="mifid_exempt_person">MiFID-exempt person</option><option value="micro_or_small_insurance_intermediary">Micro / small insurance intermediary</option><option value="post_office_giro_institution">Post office giro institution</option><option value="member_state_excluded_credit_institution">Member-State-excluded credit institution</option><option value="other">Other — review needed</option><option value="not_determined">Not determined</option></select>{[["eu_financial_entity", "Article 2 financial entity"], ["dora_eu_operating_nexus", "EU operating nexus"], ["dora_group_context", "Assessed in group context"], ["dora_ict_third_party_provider", "ICT third-party provider"], ["dora_critical_ict_provider_designated", "Designated critical ICT provider"], ["dora_scope_confirmed", "Scope reviewed and confirmed"]].map(([name, label]) => <select key={name} name={name} defaultValue="" aria-label={label} className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="">{label}: unknown</option><option value="yes">{label}: yes</option><option value="no">{label}: no</option></select>)}</div><p className="text-xs text-slate-400">Financial-entity scope and critical ICT-provider oversight are recorded separately.</p></fieldset>
        <fieldset className="grid gap-2 rounded-lg border border-zinc-700 p-3 sm:col-span-3"><legend className="px-2 text-sm font-semibold text-red-400">Other confirmed regulatory scope facts</legend><div className="grid gap-2 sm:grid-cols-2"><label className="flex items-center gap-2 text-sm"><input name="sox" type="checkbox" /> Exchange Act reporting company</label><label className="flex items-center gap-2 text-sm"><input name="mas_trm" type="checkbox" /> Subject to an MAS TRM Notice</label></div></fieldset>
        <fieldset className="grid gap-2 rounded-lg border border-zinc-700 p-3 sm:col-span-3"><legend className="px-2 text-sm font-semibold text-red-400">Contract and assurance objectives</legend><div className="flex flex-wrap gap-5"><label className="flex items-center gap-2 text-sm"><input name="pci" type="checkbox" /> PCI DSS 4.0.1</label><label className="flex items-center gap-2 text-sm"><input name="soc2" type="checkbox" /> SOC 2 readiness</label><label className="flex items-center gap-2 text-sm"><input name="iso" type="checkbox" /> ISO 27001 readiness</label><label className="flex items-center gap-2 text-sm"><input name="nist" type="checkbox" /> NIST SP 800-53 alignment</label></div><div className="mt-2 grid gap-3 sm:grid-cols-3"><select name="assurance_basis" defaultValue="customer_contract" className="rounded-lg border border-zinc-700 bg-black px-3 py-2"><option value="customer_contract">Customer or contract</option><option value="company_strategy">Company strategy</option><option value="regulator_request">Regulator request</option></select><input name="target_date" type="date" aria-label="Target completion date" className="rounded-lg border border-zinc-700 bg-black px-3 py-2" /><input name="assurance_scope" maxLength={500} placeholder="Scope, e.g. cardholder data environment" className="rounded-lg border border-zinc-700 bg-black px-3 py-2" /></div></fieldset>
        <button className="rounded-lg bg-red-400 px-4 py-2 font-semibold text-slate-950 hover:bg-red-300 sm:col-span-3">Create and evaluate</button>
      </form>
      {result && <p className="mt-4 text-sm font-medium text-emerald-300">{result}</p>}
      {error && <p role="alert" className="mt-4 text-sm text-rose-300">{error}</p>}
      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        {engagements.map((engagement) => <article key={engagement.id} className="rounded-xl border border-zinc-800 bg-black/70 p-4"><h3 className="font-semibold">{engagement.company.company_name}</h3><p className="mt-2 text-sm text-slate-400">{engagement.company.domain} · {engagement.regulations.join(", ") || "No matched regulation"}</p>{engagement.assurance_objectives.length > 0 && <div className="mt-3 flex flex-wrap gap-2">{engagement.assurance_objectives.map((objective) => <span key={objective.framework} className="rounded-full bg-violet-400/10 px-2 py-1 text-xs text-violet-300">{objective.framework} · {objective.basis.replaceAll("_", " ")}</span>)}</div>}<label className="mt-3 block cursor-pointer text-sm font-medium text-red-400">Attach PDF or DOCX<input type="file" accept=".pdf,.docx" className="sr-only" onChange={(event) => { const file = event.target.files?.[0]; if (file) upload(engagement.id, file); }} /></label><button onClick={() => inspectPosture(engagement.id)} className="mt-3 block text-sm font-medium text-red-400 hover:text-red-300">Run passive posture check</button><button onClick={() => inspectCoverage(engagement.id)} className="mt-3 block text-sm font-medium text-red-400 hover:text-red-300">View coverage matrix</button><button onClick={() => inspectReadiness(engagement.id)} className="mt-3 block text-sm font-medium text-violet-300 hover:text-violet-200">View assurance readiness</button><button onClick={() => createAuditShare(engagement.id)} className="mt-3 block text-sm font-medium text-red-400 hover:text-red-300">Create 24-hour audit link</button><button onClick={() => remove(engagement.id)} className="mt-3 text-sm font-medium text-rose-300 hover:text-rose-200">Delete engagement</button></article>)}
      </div>
      {readiness.length > 0 && <section className="mt-8 grid gap-3 sm:grid-cols-3" aria-label="Assurance readiness">{readiness.map((item) => <article key={item.framework} className="rounded-xl border border-violet-400/20 bg-violet-400/[0.05] p-4"><h3 className="font-semibold text-violet-200">{item.framework} {item.version}</h3><p className="mt-3 text-2xl font-semibold">{item.total ? Math.round(((item.covered + item.partial * 0.5) / item.total) * 100) : 0}%</p><p className="mt-2 text-xs text-slate-400">{item.covered} covered · {item.partial} partial · {item.missing} missing · {item.not_assessed} not assessed</p></article>)}</section>}
      {auditShare && <div className="mt-5 break-all rounded-lg border border-emerald-400/20 p-3 text-sm text-emerald-300">Audit link: <a className="underline" href={auditShare.url}>{auditShare.url}</a><button type="button" onClick={revokeAuditShare} className="ml-4 text-rose-300">Revoke</button></div>}
      {coverage && coverage.length > 0 && <div className="mt-8"><CoverageMatrix rows={coverage} /></div>}
    </section>
  );
}
