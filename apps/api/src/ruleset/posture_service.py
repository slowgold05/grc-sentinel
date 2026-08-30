from collections.abc import Callable
from uuid import UUID

import httpx
from sqlalchemy import Engine, text

from ruleset.intake.models import CompanyIntake
from ruleset.osint.cache import cache_result, load_cached_result
from ruleset.osint.certificate_transparency import (
    CertificateFootprint,
    fetch_certificate_footprint,
)
from ruleset.osint.dns_posture import DnsPosture, inspect_dns_posture
from ruleset.osint.homepage import HomepagePosture, inspect_homepage
from ruleset.osint.security_headers import HeaderPosture
from ruleset.osint.snapshot import SecurityPostureSnapshot, build_snapshot


def collect_posture(
    engine: Engine,
    org_id: UUID,
    engagement_id: UUID,
    *,
    dns_check: Callable[[str], DnsPosture] = inspect_dns_posture,
    certificate_check: Callable[[str], CertificateFootprint] = fetch_certificate_footprint,
    homepage_check: Callable[[str], HomepagePosture] = inspect_homepage,
) -> SecurityPostureSnapshot:
    """Collect or reuse a tenant's passive public security posture."""
    with engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        company = connection.execute(
            text("SELECT company FROM engagements WHERE id = :id"), {"id": engagement_id}
        ).scalar_one_or_none()
    if company is None:
        raise LookupError("engagement not found")
    intake = CompanyIntake.model_validate(company)
    cached = load_cached_result(engine, org_id, intake.domain, "snapshot")
    if cached is not None:
        return SecurityPostureSnapshot.model_validate(cached)
    dns = dns_check(intake.domain)
    certificates = certificate_check(intake.domain)
    try:
        homepage = homepage_check(intake.domain)
    except (ValueError, httpx.HTTPError):
        homepage = HomepagePosture(
            headers=HeaderPosture(present=[], missing=[], grade="unknown"), technologies=[]
        )
    snapshot = build_snapshot(intake, dns, certificates, homepage)
    cache_result(engine, org_id, intake.domain, "snapshot", snapshot.model_dump(mode="json"))
    return snapshot
