from ruleset.osint.homepage import inspect_homepage
from ruleset.osint.safe_url import PublicPage


def test_reuses_one_page_for_headers_and_technology_signals() -> None:
    calls: list[str] = []

    def fetch(url: str) -> PublicPage:
        calls.append(url)
        return PublicPage(
            url=url,
            headers={"server": "cloudflare", "x-frame-options": "DENY"},
            body=b'<script src="/_next/static/app.js"></script>',
        )

    posture = inspect_homepage("Example.COM", fetch=fetch)
    assert calls == ["https://example.com"]
    assert posture.technologies == ["Cloudflare", "Next.js"]
    assert "X-Frame-Options" in posture.headers.present
