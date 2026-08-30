import pytest
import httpx

from ruleset.osint.safe_url import fetch_public_page, validate_public_url


def resolver_for(address: str):
    return lambda *_: [(2, 1, 6, "", (address, 443))]


def test_accepts_public_https_and_rejects_ssrf_targets() -> None:
    assert validate_public_url("https://example.com", resolver_for("93.184.216.34"))
    for url, address in (
        ("http://metadata.test/latest", "169.254.169.254"),
        ("https://internal.test", "10.0.0.2"),
        ("https://[::1]", "::1"),
    ):
        with pytest.raises(ValueError, match="non-public"):
            validate_public_url(url, resolver_for(address))

    with pytest.raises(ValueError, match="credentials"):
        validate_public_url("https://admin:secret@example.com", resolver_for("93.184.216.34"))


def test_fetch_revalidates_redirects_and_caps_response_size() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "example.com":
            return httpx.Response(302, headers={"location": "http://internal.test/secret"})
        return httpx.Response(200, content=b"secret")

    def resolver(host: str, *_):
        address = "93.184.216.34" if host == "example.com" else "10.0.0.2"
        return [(2, 1, 6, "", (address, 443))]

    with pytest.raises(ValueError, match="non-public"):
        fetch_public_page("https://example.com", resolver=resolver, transport=httpx.MockTransport(handler))

    transport = httpx.MockTransport(lambda _: httpx.Response(200, content=b"12345"))
    with pytest.raises(ValueError, match="size limit"):
        fetch_public_page(
            "https://example.com",
            resolver=resolver_for("93.184.216.34"),
            transport=transport,
            max_bytes=4,
        )
