"""Smoke-test the deployed portfolio and capture the reviewer walkthrough."""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as conditions
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait

DEFAULT_URL = "https://sentinel-grc-ai.vercel.app"
PUBLIC_PAGES = {
    "04-risks.png": ("/risks", "Risk register"),
    "05-monitoring.png": ("/monitoring", "Monitoring"),
    "06-questionnaires.png": ("/questionnaires", "Questionnaires"),
    "07-framework-drift.png": ("/framework-drift", "Framework changes"),
    "08-policies.png": ("/policies", "Policies"),
    "09-trust-center.png": ("/trust", "Platform safeguards"),
    "11-ai-systems.png": ("/ai-systems", "AI systems"),
}


def screenshot(driver: webdriver.Chrome, path: Path) -> None:
    """Save a full-page PNG through Chrome's native capture command."""
    for logo in driver.find_elements(By.CSS_SELECTOR, ".brand-mark img, .auth-brand"):
        WebDriverWait(driver, 20).until(lambda page: page.execute_script(
            "return arguments[0].complete && arguments[0].naturalWidth > 0", logo,
        ))
    # Background Chrome tabs can pause animation frames indefinitely.
    driver.execute_script("window.scrollTo(0, 0)")
    payload = driver.execute_cdp_cmd(
        "Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True}
    )
    path.write_bytes(base64.b64decode(payload["data"]))


def set_date(driver: webdriver.Chrome, element: object, value: str) -> None:
    """Set an ISO date without relying on the workstation's input locale."""
    driver.execute_script(
        "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles:true})); arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
        element,
        value,
    )


def check_audit_layout(driver: webdriver.Chrome) -> None:
    """Require the shared report shell, both themes, responsive facts, and print styling."""
    wait = WebDriverWait(driver, 20)
    assert driver.find_elements(By.CSS_SELECTOR, ".app-shell .site-header")
    assert driver.find_elements(By.CSS_SELECTOR, ".site-header .brand-mark img")
    assert not driver.find_elements(By.CLASS_NAME, "workspace-nav")
    report = driver.find_element(By.CLASS_NAME, "audit-report")
    assert not report.find_elements(By.CSS_SELECTOR, "form, input, textarea, select")
    theme = driver.find_element(By.CLASS_NAME, "theme-toggle")
    original = driver.execute_script("return document.documentElement.dataset.theme")
    backgrounds = []
    try:
        for mode in ("light", "dark"):
            if driver.execute_script("return document.documentElement.dataset.theme") != mode:
                theme.click()
            wait.until(lambda page: page.execute_script("return document.documentElement.dataset.theme") == mode)
            backgrounds.append(driver.execute_script("return getComputedStyle(document.querySelector('.app-shell')).backgroundColor"))
            for panel in report.find_elements(By.CLASS_NAME, "surface"):
                assert driver.execute_script("return parseFloat(getComputedStyle(arguments[0]).borderTopLeftRadius) <= 2", panel)
            for width in (1440, 390, 320):
                driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {"width": width, "height": 1000, "deviceScaleFactor": 1, "mobile": False})
                assert driver.execute_script("return document.documentElement.scrollWidth <= innerWidth"), "Audit report overflows"
        assert backgrounds[0] != backgrounds[1], "Audit theme did not change"
        driver.execute_cdp_cmd("Emulation.setEmulatedMedia", {"media": "print"})
        assert driver.execute_script("return getComputedStyle(document.querySelector('.site-header')).display") == "none"
        for panel in report.find_elements(By.CLASS_NAME, "surface"):
            assert driver.execute_script("return getComputedStyle(arguments[0]).backgroundColor", panel) == "rgb(255, 255, 255)"
    finally:
        driver.execute_cdp_cmd("Emulation.setEmulatedMedia", {"media": ""})
        driver.execute_cdp_cmd("Emulation.clearDeviceMetricsOverride", {})
        if driver.execute_script("return document.documentElement.dataset.theme") != original:
            theme.click()


def engagement_diagnostics(driver: webdriver.Chrome) -> str:
    """Return status-only browser diagnostics without request headers or tokens."""
    details = []
    for entry in driver.get_log("performance"):
        message = json.loads(entry["message"])["message"]
        params = message.get("params", {})
        response = params.get("response", {})
        url = response.get("url", "")
        if message["method"] == "Network.responseReceived" and "/api/engagements" in url:
            details.append(f"HTTP {response['status']:.0f} {url}")
        if message["method"] == "Network.loadingFailed":
            details.append(f"network failure: {params.get('errorText', 'unknown')}")
    if any("blocked by CORS policy" in entry["message"] for entry in driver.get_log("browser")):
        details.append("browser: request blocked by CORS policy")
    return "; ".join(details) or "no browser diagnostic was emitted"


def open_page(driver: webdriver.Chrome, base_url: str, route: str, heading: str) -> None:
    """Open one route and require its primary heading."""
    driver.get(f"{base_url}{route}")
    WebDriverWait(driver, 20).until(
        conditions.text_to_be_present_in_element((By.TAG_NAME, "h1"), heading)
    )


def capture_ai_governance(driver: webdriver.Chrome, base_url: str, output: Path) -> None:
    """Create one fictional AI inventory record and its scoped audit share."""
    open_page(driver, base_url, "/ai-systems", "AI systems")
    form = WebDriverWait(driver, 20).until(
        conditions.presence_of_element_located((By.ID, "new-ai-system"))
    )
    Select(form.find_element(By.NAME, "engagement_id")).select_by_index(1)
    values = {
        "name": "LedgerPeak Support Assistant",
        "owner": "Customer Operations",
        "business_purpose": "Draft support replies for human review",
        "description": "Local RAG assistant with no external actions",
        "model_name": "qwen3:14b",
        "vendor": "Ollama local",
        "hosting_region": "Local workstation",
        "data_use_terms": "Local processing; no vendor training use",
        "subprocessors": "None declared",
        "security_artifacts": "Local architecture review",
        "intended_users": "Support agents",
        "affected_persons": "Customers",
        "data_categories": "Support tickets",
        "geographies": "United States, Singapore",
        "autonomy": "Drafting only",
        "decision_impact": "A human decides whether to send every answer",
        "human_oversight": "Every output is reviewed by a support agent",
    }
    for name, value in values.items():
        form.find_element(By.NAME, name).send_keys(value)
    set_date(driver, form.find_element(By.NAME, "contract_date"), "2026-09-01")
    set_date(driver, form.find_element(By.NAME, "vendor_review_date"), "2026-09-11")
    Select(form.find_element(By.NAME, "human_review_coverage")).select_by_value("every_output")
    form.find_element(By.XPATH, ".//button[normalize-space()='Register system']").click()
    WebDriverWait(driver, 30).until(conditions.element_to_be_clickable(
        (By.XPATH, "//button[normalize-space()='Create 24-hour audit share']"),
    ))
    screenshot(driver, output / "11-ai-systems.png")
    driver.find_element(
        By.XPATH, "//button[normalize-space()='Create 24-hour audit share']"
    ).click()
    link = (
        WebDriverWait(driver, 20)
        .until(
            conditions.presence_of_element_located(
                (By.XPATH, "//a[contains(@href, '/audit/share/')]")
            )
        )
        .get_attribute("href")
    )
    driver.get(link)
    WebDriverWait(driver, 20).until(
        conditions.text_to_be_present_in_element((By.TAG_NAME, "body"), "AI system record")
    )
    check_audit_layout(driver)
    screenshot(driver, output / "12-ai-audit-share.png")


def capture_walkthrough(driver: webdriver.Chrome, base_url: str, output: Path) -> None:
    """Capture the fictional signed-in walkthrough after one manual Clerk login."""
    driver.get(f"{base_url}/workspace")
    try:
        driver.find_element(By.XPATH, "//button[normalize-space()='Sign in']").click()
    except Exception:
        pass
    print("Complete Clerk sign-in, open Workspace, and select your Sentinel GRC organization in Chrome.")
    try:
        WebDriverWait(driver, 600).until(
            conditions.presence_of_element_located((By.ID, "new-engagement"))
        )
    except TimeoutException as error:
        raise RuntimeError("Clerk sign-in or organization selection was not completed") from error
    time.sleep(3)  # Clerk may render the user before the organization-scoped token is ready.

    form = driver.find_element(By.CSS_SELECTOR, "form")
    form.find_element(By.NAME, "company_name").send_keys("LedgerPeak Payments")
    form.find_element(By.NAME, "domain").send_keys("example.com")
    form.find_element(By.NAME, "employee_count").send_keys("85")
    for name in (
        "us",
        "financial_services",
        "card_data",
        "securities",
        "california",
        "eu",
        "singapore",
        "public_company",
    ):
        form.find_element(By.NAME, name).click()
    form.find_element(
        By.XPATH, ".//button[normalize-space()='Continue to regulatory review →']"
    ).click()
    Select(form.find_element(By.NAME, "ftc_financial_institution")).select_by_value("yes")
    Select(form.find_element(By.NAME, "customer_financial_information")).select_by_value("yes")
    Select(form.find_element(By.NAME, "glba_other_regulator")).select_by_value("no")
    Select(form.find_element(By.NAME, "glba_financial_activity")).select_by_value("finance_company")
    form.find_element(By.NAME, "glba_customer_count").send_keys("12000")
    form.find_element(By.XPATH, ".//button[contains(., 'PCI DSS')]").click()
    Select(form.find_element(By.NAME, "pci_entity_role")).select_by_value("merchant")
    for name in (
        "pci_stores_account_data",
        "pci_processes_account_data",
        "pci_transmits_account_data",
        "pci_can_impact_cde",
        "pci_cde_scope_confirmed",
    ):
        Select(form.find_element(By.NAME, name)).select_by_value("yes")
    Select(form.find_element(By.NAME, "pci_fully_outsourced")).select_by_value("no")
    Select(form.find_element(By.NAME, "pci_validation_method")).select_by_value("saq_d_merchant")
    form.find_element(By.XPATH, ".//button[contains(., 'Regulation S-P')]").click()
    Select(form.find_element(By.NAME, "reg_sp_covered_institution")).select_by_value("yes")
    Select(form.find_element(By.NAME, "reg_sp_entity_type")).select_by_value("broker_dealer")
    Select(form.find_element(By.NAME, "reg_sp_size_cohort")).select_by_value("larger")
    Select(form.find_element(By.NAME, "reg_sp_customer_information")).select_by_value("yes")
    Select(form.find_element(By.NAME, "reg_sp_service_provider_used")).select_by_value("yes")
    form.find_element(By.XPATH, ".//button[contains(., 'FINRA')]").click()
    Select(form.find_element(By.NAME, "finra_member")).select_by_value("yes")
    Select(form.find_element(By.NAME, "finra_firm_type")).select_by_value("carrying_clearing")
    Select(form.find_element(By.NAME, "finra_customer_accounts")).select_by_value("yes")
    Select(form.find_element(By.NAME, "finra_mission_critical_systems_identified")).select_by_value(
        "yes"
    )
    Select(form.find_element(By.NAME, "finra_bcp_scope_confirmed")).select_by_value("yes")
    form.find_element(By.XPATH, ".//button[contains(., 'NYDFS')]").click()
    Select(form.find_element(By.NAME, "nydfs_licensed")).select_by_value("yes")
    Select(form.find_element(By.NAME, "nydfs_authorization_type")).select_by_value(
        "financial_services"
    )
    Select(form.find_element(By.NAME, "nydfs_exemption")).select_by_value("none")
    Select(form.find_element(By.NAME, "nydfs_class_a_company")).select_by_value("no")
    Select(form.find_element(By.NAME, "nydfs_uses_affiliate_program")).select_by_value("no")
    form.find_element(By.XPATH, ".//button[contains(., 'CCPA')]").click()
    for name in (
        "ccpa_covered_business",
        "california_consumer_data",
        "ccpa_for_profit",
        "ccpa_does_business_in_california",
        "ccpa_determines_processing_purposes",
    ):
        Select(form.find_element(By.NAME, name)).select_by_value("yes")
    Select(form.find_element(By.NAME, "ccpa_related_entity")).select_by_value("no")
    Select(form.find_element(By.NAME, "ccpa_exemption")).select_by_value("none")
    form.find_element(By.NAME, "ccpa_threshold_year").send_keys("2025")
    form.find_element(By.NAME, "ccpa_gross_revenue_usd").send_keys("30000000")
    form.find_element(By.NAME, "ccpa_consumers_or_households").send_keys("120000")
    form.find_element(By.NAME, "ccpa_selling_sharing_revenue_percent").send_keys("10")
    form.find_element(By.XPATH, ".//button[contains(., 'DORA')]").click()
    Select(form.find_element(By.NAME, "dora_entity_type")).select_by_value("payment_institution")
    Select(form.find_element(By.NAME, "dora_article_2_exclusion")).select_by_value("none")
    for name in (
        "eu_financial_entity",
        "dora_eu_operating_nexus",
        "dora_group_context",
        "dora_ict_third_party_provider",
        "dora_scope_confirmed",
    ):
        Select(form.find_element(By.NAME, name)).select_by_value("yes")
    Select(form.find_element(By.NAME, "dora_critical_ict_provider_designated")).select_by_value(
        "no"
    )
    form.find_element(By.XPATH, ".//button[contains(., 'MAS TRM')]").click()
    Select(form.find_element(By.NAME, "mas_institution_type")).select_by_value(
        "payment_or_dpt_entity"
    )
    Select(form.find_element(By.NAME, "mas_trm_notice_number")).select_by_value("FSM-N13")
    for name in (
        "mas_trm_notice_subject",
        "mas_licence_or_approval_confirmed",
        "mas_legacy_notice_transition_complete",
        "mas_customer_information_handled",
        "mas_critical_system_framework_established",
        "mas_critical_systems_identified",
        "mas_scope_confirmed",
    ):
        Select(form.find_element(By.NAME, name)).select_by_value("yes")
    form.find_element(By.XPATH, ".//button[contains(., 'SOX 404')]").click()
    Select(form.find_element(By.NAME, "sox_filer_category")).select_by_value("accelerated_filer")
    set_date(driver, form.find_element(By.NAME, "sox_reporting_period_end"), "2025-12-31")
    Select(form.find_element(By.NAME, "sox_management_assessment_status")).select_by_value(
        "effective"
    )
    Select(form.find_element(By.NAME, "sox_attestation_status")).select_by_value("unqualified")
    for name in (
        "exchange_act_reporting_company",
        "sox_management_icfr_assessment_required",
        "sox_auditor_attestation_required",
        "sox_scope_confirmed",
    ):
        Select(form.find_element(By.NAME, name)).select_by_value("yes")
    for name in ("pci", "soc2"):
        form.find_element(By.NAME, name).click()
    screenshot(driver, output / "02-intake.png")
    form.find_element(
        By.XPATH, ".//button[normalize-space()='Review and create assessment']"
    ).click()
    WebDriverWait(driver, 30).until(
        lambda page: page.find_elements(
            By.XPATH, "//button[normalize-space()='Create audit link']"
        )
        or page.find_elements(By.CSS_SELECTOR, "[role='alert']")
    )
    errors = driver.find_elements(By.CSS_SELECTOR, "[role='alert']")
    if errors:
        raise RuntimeError(
            f"Engagement creation failed: {errors[0].text}; {engagement_diagnostics(driver)}"
        )
    open_page(driver, base_url, "", "Compliance, with the evidence to back it.")
    screenshot(driver, output / "01-overview.png")
    driver.get(f"{base_url}/demo#assessment")
    WebDriverWait(driver, 20).until(conditions.element_to_be_clickable(
        (By.XPATH, "//summary[contains(., 'Event logging')]"),
    )).click()
    # This is an illustrative quote, not the newly created engagement's analysis.
    screenshot(driver, output / "03-coverage.png")

    for filename, (route, heading) in PUBLIC_PAGES.items():
        open_page(driver, base_url, route, heading)
        screenshot(driver, output / filename)

    capture_ai_governance(driver, base_url, output)

    driver.get(f"{base_url}/workspace")
    WebDriverWait(driver, 20).until(
        conditions.element_to_be_clickable(
            (By.XPATH, "//button[normalize-space()='Create audit link']")
        )
    ).click()
    link = (
        WebDriverWait(driver, 20)
        .until(
            conditions.presence_of_element_located(
                (By.XPATH, "//a[contains(@href, '/audit/share/')]")
            )
        )
        .get_attribute("href")
    )
    driver.get(link)
    WebDriverWait(driver, 20).until(
        lambda page: page.find_elements(By.XPATH, "//h2[normalize-space()='Company profile']")
        or page.find_elements(By.CSS_SELECTOR, "[role='alert']")
    )
    errors = driver.find_elements(By.CSS_SELECTOR, "[role='alert']")
    if errors:
        raise RuntimeError(f"Audit share failed: {errors[0].text}")
    check_audit_layout(driver)
    screenshot(driver, output / "10-audit-share.png")


def main() -> None:
    """Run public smoke checks and optionally the authenticated capture flow."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_URL)
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1440,1100")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"})
    if args.headless:
        options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    try:
        open_page(driver, args.base_url, "", "Compliance, with the evidence to back it.")
        assert "Example workspace" in driver.find_element(By.CLASS_NAME, "product-preview").text
        for route, heading in PUBLIC_PAGES.values():
            open_page(driver, args.base_url, route, heading)
        if args.capture:
            output = Path(__file__).resolve().parents[3] / "screenshots"
            capture_walkthrough(driver, args.base_url, output)
    finally:
        driver.quit()
    print("Selenium portfolio smoke test passed.")


if __name__ == "__main__":
    main()
