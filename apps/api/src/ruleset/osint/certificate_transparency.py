import json
from typing import Literal

import httpx
from pydantic import BaseModel

from ruleset.osint.dns_posture import normalize_domain


class CertificateFootprint(BaseModel):
    """Subdomains observed in public certificate-transparency records."""

    status: Literal["known", "unknown"]
    subdomains: list[str]


def fetch_certificate_footprint(
    domain: str,
    *,
    transport: httpx.BaseTransport | None = None,
    max_bytes: int = 2_000_000,
) -> CertificateFootprint:
    """Query the pinned crt.sh API and return validated names under the domain."""
    domain = normalize_domain(domain)
    try:
        with httpx.Client(base_url="https://crt.sh", transport=transport, timeout=10) as client:
            with client.stream("GET", "/", params={"q": f"%.{domain}", "output": "json"}) as response:
                response.raise_for_status()
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > max_bytes:
                        return CertificateFootprint(status="unknown", subdomains=[])
        records = json.loads(body)
    except (httpx.HTTPError, json.JSONDecodeError):
        return CertificateFootprint(status="unknown", subdomains=[])

    names: set[str] = set()
    for record in records if isinstance(records, list) else []:
        for candidate in str(record.get("name_value", "")).splitlines():
            candidate = candidate.removeprefix("*.").lower().rstrip(".")
            if candidate == domain or candidate.endswith(f".{domain}"):
                try:
                    names.add(normalize_domain(candidate))
                except ValueError:
                    continue
    return CertificateFootprint(status="known", subdomains=sorted(names))
