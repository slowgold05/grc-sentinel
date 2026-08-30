import pytest

from ruleset.osint.dns_posture import inspect_dns_posture, normalize_domain


def test_inspects_email_authentication_records() -> None:
    records = {
        "example.com": ["v=spf1 include:_spf.example.net -all"],
        "_dmarc.example.com": ["v=DMARC1; p=reject"],
        "mail._domainkey.example.com": ["v=DKIM1; p=abc"],
    }
    posture = inspect_dns_posture(
        "Example.COM.", selector="mail", lookup=lambda name: records.get(name, [])
    )
    assert (posture.spf, posture.dmarc, posture.dkim) == ("hardfail", "enforce", "present")
    assert inspect_dns_posture("example.com", lookup=lambda _: []).dkim == "unknown"


def test_rejects_non_domain_input() -> None:
    with pytest.raises(ValueError, match="invalid domain"):
        normalize_domain("https://example.com/path")
