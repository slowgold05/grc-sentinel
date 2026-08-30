from collections.abc import Callable
from typing import Literal

import dns.exception
import dns.resolver
from pydantic import BaseModel


TxtLookup = Callable[[str], list[str]]


class DnsPosture(BaseModel):
    """Email authentication posture inferred from public DNS TXT records."""

    domain: str
    spf: Literal["absent", "present", "softfail", "hardfail"]
    dmarc: Literal["absent", "monitor", "enforce"]
    dkim: Literal["unknown", "absent", "present"]


def normalize_domain(domain: str) -> str:
    """Normalize and validate a user-supplied DNS name."""
    value = domain.rstrip(".").encode("idna").decode("ascii").lower()
    labels = value.split(".")
    if len(value) > 253 or len(labels) < 2 or any(
        not label or len(label) > 63 or label.startswith("-") or label.endswith("-")
        for label in labels
    ):
        raise ValueError("invalid domain")
    if any(not all(character.isalnum() or character == "-" for character in label) for label in labels):
        raise ValueError("invalid domain")
    return value


def lookup_txt(name: str) -> list[str]:
    """Return public TXT records, degrading DNS failures to no observations."""
    try:
        return [record.to_text().strip('"').replace('" "', "") for record in dns.resolver.resolve(name, "TXT")]
    except dns.exception.DNSException:
        return []


def inspect_dns_posture(
    domain: str, *, selector: str | None = None, lookup: TxtLookup = lookup_txt
) -> DnsPosture:
    """Inspect SPF, DMARC, and an optional known DKIM selector."""
    domain = normalize_domain(domain)
    spf_record = next((item for item in lookup(domain) if item.lower().startswith("v=spf1")), "")
    mechanisms = spf_record.lower().split()
    spf = "hardfail" if "-all" in mechanisms else "softfail" if "~all" in mechanisms else "present" if spf_record else "absent"

    dmarc_record = next(
        (item.lower() for item in lookup(f"_dmarc.{domain}") if item.lower().startswith("v=dmarc1")),
        "",
    )
    tags = dict(
        part.strip().split("=", 1)
        for part in dmarc_record.split(";")
        if "=" in part
    )
    dmarc = "enforce" if tags.get("p") in {"reject", "quarantine"} else "monitor" if tags.get("p") == "none" else "absent"

    dkim = "unknown"
    if selector:
        selector = selector.lower()
        if "." in selector or normalize_domain(f"{selector}.{domain}") != f"{selector}.{domain}":
            raise ValueError("invalid DKIM selector")
        records = lookup(f"{selector}._domainkey.{domain}")
        dkim = "present" if any(item.lower().startswith("v=dkim1") for item in records) else "absent"
    return DnsPosture(domain=domain, spf=spf, dmarc=dmarc, dkim=dkim)
