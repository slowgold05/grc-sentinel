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
        "ftc_financial_institution",
        "customer_financial_information",
        "cardholder_data",
        "reg_sp",
        "finra",
        "nydfs",
        "sox",
        "ccpa",
        "dora",
        "mas_trm",
        "pci",
        "soc2",
    ):
        form.find_element(By.NAME, name).click()
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
