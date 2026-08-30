from collections.abc import Callable
from html.parser import HTMLParser

from pydantic import BaseModel

from ruleset.osint.dns_posture import normalize_domain
from ruleset.osint.safe_url import PublicPage, fetch_public_page
from ruleset.osint.security_headers import HeaderPosture, grade_security_headers


class _Signals(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.values: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "meta" and attributes.get("name", "").lower() == "generator":
            self.values.append(attributes.get("content", ""))
        if tag == "script":
            self.values.append(attributes.get("src", ""))


class HomepagePosture(BaseModel):
    """Security headers and conservative technology signals from one request."""

    headers: HeaderPosture
    technologies: list[str]


def inspect_homepage(
    domain: str, *, fetch: Callable[[str], PublicPage] = fetch_public_page
) -> HomepagePosture:
    """Inspect a public homepage without making duplicate requests."""
    page = fetch(f"https://{normalize_domain(domain)}")
    parser = _Signals()
    parser.feed(page.body.decode("utf-8", errors="replace"))
    signals = " ".join(
        [*parser.values, page.headers.get("server", ""), page.headers.get("x-powered-by", "")]
    ).lower()
    # ponytail: conservative signatures only; add a fingerprint database when breadth matters.
    signatures = {
        "Cloudflare": "cloudflare",
        "Next.js": "/_next/",
        "WordPress": "wordpress",
    }
    technologies = sorted(name for name, marker in signatures.items() if marker in signals)
    return HomepagePosture(headers=grade_security_headers(page.headers), technologies=technologies)
