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

DEFAULT_URL = "https://grc-sentinel-slowgold05s-projects.vercel.app"
PUBLIC_PAGES = {
    "04-risks.png": ("/risks", "Risk, linked to controls."),
    "05-monitoring.png": ("/monitoring", "Policy says it. Systems prove it."),
    "06-questionnaires.png": ("/questionnaires", "Security questionnaire answers"),
    "07-framework-drift.png": ("/framework-drift", "Regulatory drift impact"),
    "08-policies.png": ("/policies", "Verified policy exports"),
    "09-trust-center.png": ("/trust", "The platform follows the controls it recommends."),
}


def screenshot(driver: webdriver.Chrome, path: Path) -> None:
    """Save a full-page PNG through Chrome's native capture command."""
    payload = driver.execute_cdp_cmd(
        "Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True}
    )
    path.write_bytes(base64.b64decode(payload["data"]))


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


def capture_walkthrough(driver: webdriver.Chrome, base_url: str, output: Path) -> None:
    """Capture the fictional signed-in walkthrough after one manual Clerk login."""
    driver.get(base_url)
    try:
        driver.find_element(By.XPATH, "//button[normalize-space()='Sign in']").click()
    except Exception:
        pass
    print("Complete Clerk sign-in and select your GRC Sentinel organization in Chrome.")
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
        "pci",
        "soc2",
    ):
        form.find_element(By.NAME, name).click()
    Select(form.find_element(By.NAME, "ftc_financial_institution")).select_by_value("yes")
    Select(form.find_element(By.NAME, "customer_financial_information")).select_by_value("yes")
    Select(form.find_element(By.NAME, "glba_other_regulator")).select_by_value("no")
    Select(form.find_element(By.NAME, "glba_financial_activity")).select_by_value("finance_company")
    form.find_element(By.NAME, "glba_customer_count").send_keys("12000")
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
    Select(form.find_element(By.NAME, "reg_sp_covered_institution")).select_by_value("yes")
    Select(form.find_element(By.NAME, "reg_sp_entity_type")).select_by_value("broker_dealer")
    Select(form.find_element(By.NAME, "reg_sp_size_cohort")).select_by_value("larger")
    Select(form.find_element(By.NAME, "reg_sp_customer_information")).select_by_value("yes")
    Select(form.find_element(By.NAME, "reg_sp_service_provider_used")).select_by_value("yes")
    Select(form.find_element(By.NAME, "finra_member")).select_by_value("yes")
    Select(form.find_element(By.NAME, "finra_firm_type")).select_by_value("carrying_clearing")
    Select(form.find_element(By.NAME, "finra_customer_accounts")).select_by_value("yes")
    Select(form.find_element(By.NAME, "finra_mission_critical_systems_identified")).select_by_value("yes")
    Select(form.find_element(By.NAME, "finra_bcp_scope_confirmed")).select_by_value("yes")
    Select(form.find_element(By.NAME, "nydfs_licensed")).select_by_value("yes")
    Select(form.find_element(By.NAME, "nydfs_authorization_type")).select_by_value("financial_services")
    Select(form.find_element(By.NAME, "nydfs_exemption")).select_by_value("none")
    Select(form.find_element(By.NAME, "nydfs_class_a_company")).select_by_value("no")
    Select(form.find_element(By.NAME, "nydfs_uses_affiliate_program")).select_by_value("no")
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
    Select(form.find_element(By.NAME, "dora_critical_ict_provider_designated")).select_by_value("no")
    Select(form.find_element(By.NAME, "mas_institution_type")).select_by_value("payment_or_dpt_entity")
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
    Select(form.find_element(By.NAME, "sox_filer_category")).select_by_value("accelerated_filer")
    form.find_element(By.NAME, "sox_reporting_period_end").send_keys("12/31/2025")
    Select(form.find_element(By.NAME, "sox_management_assessment_status")).select_by_value("effective")
    Select(form.find_element(By.NAME, "sox_attestation_status")).select_by_value("unqualified")
    for name in (
        "exchange_act_reporting_company",
        "sox_management_icfr_assessment_required",
        "sox_auditor_attestation_required",
        "sox_scope_confirmed",
    ):
        Select(form.find_element(By.NAME, name)).select_by_value("yes")
    screenshot(driver, output / "02-intake.png")
    form.find_element(By.XPATH, ".//button[normalize-space()='Create and evaluate']").click()
    WebDriverWait(driver, 30).until(
        lambda page: page.find_elements(
            By.XPATH, "//button[normalize-space()='Create 24-hour audit link']"
        )
        or page.find_elements(By.CSS_SELECTOR, "[role='alert']")
    )
    errors = driver.find_elements(By.CSS_SELECTOR, "[role='alert']")
    if errors:
        raise RuntimeError(
            f"Engagement creation failed: {errors[0].text}; {engagement_diagnostics(driver)}"
        )
    screenshot(driver, output / "01-overview.png")
    driver.find_element(By.XPATH, "//button[.//span[normalize-space()='AU-2']]").click()
    screenshot(driver, output / "03-coverage.png")

    for filename, (route, heading) in PUBLIC_PAGES.items():
        open_page(driver, base_url, route, heading)
        screenshot(driver, output / filename)

    driver.get(base_url)
    WebDriverWait(driver, 20).until(
        conditions.element_to_be_clickable(
            (By.XPATH, "//button[normalize-space()='Create 24-hour audit link']")
        )
    ).click()
    link = WebDriverWait(driver, 20).until(
        conditions.presence_of_element_located((By.XPATH, "//a[contains(@href, '/audit/share/')]") )
    ).get_attribute("href")
    driver.get(link)
    WebDriverWait(driver, 20).until(
        lambda page: page.find_elements(By.XPATH, "//h2[normalize-space()='Company profile']")
        or page.find_elements(By.CSS_SELECTOR, "[role='alert']")
    )
    errors = driver.find_elements(By.CSS_SELECTOR, "[role='alert']")
    if errors:
        raise RuntimeError(f"Audit share failed: {errors[0].text}")
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
        open_page(driver, args.base_url, "", "Control coverage, with proof.")
        assert "Fintech scoping perimeter" in driver.page_source
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
