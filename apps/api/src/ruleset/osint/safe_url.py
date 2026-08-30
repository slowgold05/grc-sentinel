import ipaddress
import socket
from collections.abc import Callable
from urllib.parse import urljoin, urlsplit

import httpx
from pydantic import BaseModel


Resolver = Callable[..., list[tuple]]


class PublicPage(BaseModel):
    """Capped public homepage response safe for deterministic analysis."""

    url: str
    headers: dict[str, str]
    body: bytes


def validate_public_url(url: str, resolver: Resolver = socket.getaddrinfo) -> str:
    """Accept only HTTP(S) URLs whose current DNS answers are globally routable."""
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("URL must use http or https and include a hostname")
    if parsed.username or parsed.password:
        raise ValueError("URL credentials are not allowed")
    try:
        answers = resolver(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as error:
        raise ValueError("hostname could not be resolved") from error
    addresses = {answer[4][0].split("%")[0] for answer in answers}
    if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise ValueError("hostname resolves to a non-public address")
    return url


def fetch_public_page(
    url: str,
    *,
    resolver: Resolver = socket.getaddrinfo,
    transport: httpx.BaseTransport | None = None,
    max_redirects: int = 3,
    max_bytes: int = 1_000_000,
) -> PublicPage:
    """Fetch a public page with redirect revalidation and a hard body-size cap."""
    with httpx.Client(transport=transport, follow_redirects=False, timeout=10) as client:
        for redirect_count in range(max_redirects + 1):
            validate_public_url(url, resolver)
            with client.stream("GET", url, headers={"Accept": "text/html"}) as response:
                if response.is_redirect:
                    if redirect_count == max_redirects or "location" not in response.headers:
                        raise ValueError("redirect limit exceeded or location missing")
                    url = urljoin(url, response.headers["location"])
                    continue
                response.raise_for_status()
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > max_bytes:
                        raise ValueError("response exceeds size limit")
                return PublicPage(
                    url=str(response.url), headers=dict(response.headers), body=bytes(body)
                )
    raise ValueError("redirect limit exceeded")
