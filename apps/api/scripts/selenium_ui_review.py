"""Check the public tour, responsive navigation, and both themes without tenant writes."""

from __future__ import annotations

import argparse
import base64
from pathlib import Path
import re

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from selenium_portfolio import check_audit_layout, screenshot


def contrast(first: str, second: str) -> float:
    """Compute WCAG contrast for two opaque computed RGB colors."""
    def luminance(color: str) -> float:
        channels = [int(value) / 255 for value in re.findall(r"\d+", color)[:3]]
        linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
        return sum(value * weight for value, weight in zip(linear, [0.2126, 0.7152, 0.0722], strict=True))

    values = sorted([luminance(first), luminance(second)])
    return (values[1] + 0.05) / (values[0] + 0.05)


def main() -> None:
    """Exercise reviewer-facing paths and save only public fictional screenshots."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:3010")
    parser.add_argument("--output", type=Path, default=Path("../../.tmp-ui-checks"))
    parser.add_argument("--capture-assets", type=Path, help="Capture the three public demo panels for the homepage, then exit.")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1100")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30)

    def open_page(route: str) -> None:
        driver.get(args.base_url.rstrip("/") + route)
        wait.until(lambda page: page.find_elements(By.TAG_NAME, "h1"))
        wait_for_account()

    def wait_for_account() -> None:
        wait.until(lambda page: any(button.text == "Sign in" and button.is_displayed() for button in page.find_elements(By.CSS_SELECTOR, ".account-controls button")))

    def capture(name: str) -> None:
        wait_for_account()
        for picture in driver.find_elements(By.CSS_SELECTOR, ".feature-image img"):
            driver.execute_script("arguments[0].scrollIntoView({block:'center'})", picture)
            wait.until(lambda page: page.execute_script("return arguments[0].complete && arguments[0].naturalWidth > 0", picture))
        driver.execute_script("document.activeElement?.blur()")
        screenshot(driver, args.output / name)

    def theme_button():
        return driver.find_element(By.CLASS_NAME, "theme-toggle")

    def check_width() -> None:
        assert driver.execute_script("return document.documentElement.scrollWidth <= innerWidth"), "Page overflows horizontally"

    try:
        if args.capture_assets:
            args.capture_assets.mkdir(parents=True, exist_ok=True)
            driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {"width": 960, "height": 1600, "deviceScaleFactor": 1, "mobile": False})
            open_page("/demo")
            if driver.execute_script("return document.documentElement.dataset.theme") != "light":
                theme_button().click()
            driver.find_element(By.CSS_SELECTOR, "#assessment summary").click()
            driver.execute_async_script("const done=arguments[0]; scrollTo(0,0); requestAnimationFrame(() => requestAnimationFrame(done));")
            for section in ["assessment", "ai-system", "policy"]:
                clip = driver.execute_script("const r=arguments[0].getBoundingClientRect(); return {x:r.left+scrollX,y:r.top+scrollY,width:r.width,height:r.height,scale:1}", driver.find_element(By.ID, section))
                result = driver.execute_cdp_cmd("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True, "clip": clip})
                (args.capture_assets / f"{section}.png").write_bytes(base64.b64decode(result["data"]))
            print("Captured three public, fictional demo panels; no tenant data accessed.")
            return
        open_page("/")
        assert driver.title == "Sentinel GRC"
        assert driver.find_element(By.CSS_SELECTOR, 'link[rel="icon"]').get_attribute("href").endswith("/brand/mark.png")
        assert len(driver.find_elements(By.CSS_SELECTOR, ".brand-mark img")) == 3
        assert not driver.find_elements(By.CLASS_NAME, "preview-mark")
        assert not driver.find_elements(By.CSS_SELECTOR, "form, #program-status")
        assert not driver.find_elements(By.CSS_SELECTOR, ".hero-orbit, .orbit-globe, .orbit-grid, .orbit-satellite")
        trails = driver.find_element(By.CLASS_NAME, "evidence-trails")
        assert trails.get_attribute("aria-hidden") == "true"
        assert [label.text for label in trails.find_elements(By.TAG_NAME, "span")] == ["Policy", "Evidence", "Review"]
        assert driver.execute_script("return getComputedStyle(arguments[0]).pointerEvents", trails) == "none"
        assert "Example workspace" in driver.find_element(By.CLASS_NAME, "product-preview").text
        assert "74%" not in driver.find_element(By.TAG_NAME, "main").text
        for mode in ["light", "dark"]:
            if driver.execute_script("return document.documentElement.dataset.theme") != mode:
                theme_button().click()
            wait.until(lambda page: page.execute_script("return document.documentElement.dataset.theme") == mode)
            for selector in ["#platform-heading", ".landing-hero .hero-muted"]:
                foreground, background = driver.execute_script(
                    "return [getComputedStyle(document.querySelector(arguments[0])).color, getComputedStyle(document.querySelector('.landing-hero')).backgroundColor]", selector,
                )
                assert contrast(foreground, background) >= 4.5, (selector, mode, foreground, background)
            capture(f"home-{mode}.png")
            driver.refresh()
            wait.until(lambda page: page.execute_script("return document.documentElement.dataset.theme") == mode)

        wait_for_account()
        ActionChains(driver).move_to_element(driver.find_element(By.CSS_SELECTOR, ".platform-menu summary")).perform()
        wait.until(lambda page: page.find_element(By.CLASS_NAME, "platform-menu").get_attribute("open"))
        driver.save_screenshot(str(args.output / "navigation.png"))
        ActionChains(driver).move_to_element(driver.find_element(By.CLASS_NAME, "brand")).perform()
        wait.until(lambda page: not page.find_element(By.CLASS_NAME, "platform-menu").get_attribute("open"))

        for width in [1440, 1024, 768, 390, 320]:
            driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {"width": width, "height": 1000, "deviceScaleFactor": 1, "mobile": False})
            check_width()
            nav = driver.find_element(By.CLASS_NAME, "site-nav")
            for link in nav.find_elements(By.CSS_SELECTOR, ":scope > a"):
                assert link.is_displayed()
                assert driver.execute_script("const r=arguments[0].getBoundingClientRect(); return r.left>=0 && r.right<=innerWidth", link), link.text
            sign_in = wait.until(lambda page: next((button for button in page.find_elements(By.TAG_NAME, "button") if button.text == "Sign in" and button.is_displayed()), False))
            assert sign_in.rect["width"] >= 44
            menu = driver.find_element(By.CSS_SELECTOR, ".platform-menu summary")
            menu.send_keys(Keys.ENTER)
            wait.until(lambda page: page.find_element(By.CLASS_NAME, "platform-menu").get_attribute("open"))
            assert driver.find_element(By.CSS_SELECTOR, '.menu-links a[href="/workspace"]').is_displayed()
            check_width()
            menu.send_keys(Keys.ESCAPE)
            assert not driver.find_element(By.CLASS_NAME, "platform-menu").get_attribute("open")
            if width == 390:
                capture("mobile.png")

        driver.execute_cdp_cmd("Emulation.setEmulatedMedia", {"features": [{"name": "prefers-reduced-motion", "value": "reduce"}]})
        assert driver.execute_script("return getComputedStyle(document.querySelector('.framework-marquee__track')).animationName") == "none"
        driver.execute_cdp_cmd("Emulation.clearDeviceMetricsOverride", {})
        driver.find_element(By.CSS_SELECTOR, '.product-jump-nav a[href="#ai-governance"]').click()
        wait.until(lambda page: page.current_url.endswith("#ai-governance"))
        for picture in driver.find_elements(By.CSS_SELECTOR, ".feature-image img"):
            wait.until(lambda page: page.execute_script("return arguments[0].complete && arguments[0].naturalWidth > 0", picture))
        assert len(driver.find_elements(By.CSS_SELECTOR, ".feature-image img")) == 3
        driver.execute_script("scrollTo(0,0)")
        driver.find_element(By.CSS_SELECTOR, '.landing-hero a[href="/demo"]').click()
        wait.until(lambda page: "/demo" in page.current_url)
        wait.until(lambda page: page.find_elements(By.ID, "assessment"))
        summary = driver.find_element(By.CSS_SELECTOR, "#assessment summary")
        summary.click()
        assert driver.find_element(By.CSS_SELECTOR, "#assessment blockquote").is_displayed()
        ai_review = driver.find_element(By.CSS_SELECTOR, "#ai-system summary")
        ai_review.click()
        assert "approval pending" in driver.find_element(By.ID, "ai-system").text.lower()
        assert driver.find_element(By.ID, "policy").is_displayed()
        capture("demo.png")
        open_page("/risks")
        assert not driver.find_element(By.ID, "risk-heatmap").get_attribute("open")
        assert len(driver.find_elements(By.CSS_SELECTOR, ".risk-table tbody tr")) == 3
        wait.until(lambda page: "Open your own workspace" in page.find_element(By.TAG_NAME, "main").text)
        capture("risks.png")
        driver.find_element(By.CSS_SELECTOR, "#risk-heatmap summary").click()
        assert driver.find_element(By.ID, "risk-heatmap").get_attribute("open")
        for route in ["/ai-systems", "/policies", "/monitoring", "/questionnaires", "/framework-drift", "/trust", "/workspace"]:
            open_page(route)
            check_width()
            logo = driver.find_element(By.CSS_SELECTOR, ".site-header .brand-mark img")
            wait.until(lambda page: page.execute_script("return arguments[0].complete && arguments[0].naturalWidth > 0", logo))
            assert driver.find_elements(By.CLASS_NAME, "page-heading")
            if route == "/ai-systems":
                assert driver.find_element(By.ID, "demo-ai-heading").is_displayed()
            if route == "/workspace":
                wait.until(lambda page: "Open your own workspace" in page.find_element(By.TAG_NAME, "main").text)
                assert not driver.find_elements(By.CSS_SELECTOR, "form.scope-form")
        open_page("/audit/share/invalid")
        wait.until(lambda page: page.find_elements(By.CSS_SELECTOR, ".audit-report [role='alert']"))
        assert "invalid, expired, or revoked" in driver.find_element(By.CSS_SELECTOR, "[role='alert']").text
        check_audit_layout(driver)
        for route in ("/sign-in", "/sign-up"):
            driver.get(args.base_url.rstrip("/") + route)
            logo = wait.until(lambda page: next(iter(page.find_elements(By.CLASS_NAME, "auth-brand")), False))
            wait.until(lambda page: page.execute_script("return arguments[0].complete && arguments[0].naturalWidth > 0", logo))
            assert logo.get_attribute("alt") == "Sentinel GRC"
            check_width()
        print("Public UI checks passed: themes/contrast, five widths, hover/keyboard menus, product images and links, demo disclosures, routes, signed-out workspace, and invalid audit-share layout.")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
