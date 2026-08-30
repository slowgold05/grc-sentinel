import httpx

from ruleset.osint.certificate_transparency import fetch_certificate_footprint


def test_returns_only_valid_names_beneath_requested_domain() -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            200,
            json=[
                {"name_value": "api.example.com\n*.www.example.com"},
                {"name_value": "attacker.example.net"},
            ],
        )
    )
    result = fetch_certificate_footprint("example.com", transport=transport)
    assert result.status == "known"
    assert result.subdomains == ["api.example.com", "www.example.com"]


def test_degrades_api_failure_to_unknown() -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(503))
    assert fetch_certificate_footprint("example.com", transport=transport).status == "unknown"
