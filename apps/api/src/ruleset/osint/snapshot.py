from pydantic import BaseModel

from ruleset.intake.models import CompanyIntake
from ruleset.osint.certificate_transparency import CertificateFootprint
from ruleset.osint.dns_posture import DnsPosture
from ruleset.osint.homepage import HomepagePosture


class SecurityPostureSnapshot(BaseModel):
    """Passive observations, safe prefills, and intake inconsistencies."""

    observations: list[str]
    prefills: dict[str, object]
    inconsistencies: list[str]


def build_snapshot(
    intake: CompanyIntake,
    dns: DnsPosture,
    certificates: CertificateFootprint,
    homepage: HomepagePosture,
) -> SecurityPostureSnapshot:
    """Synthesize deterministic OSINT observations without blocking intake."""
    observations = [
        f"Security header grade: {homepage.headers.grade}",
        f"Certificate names observed: {len(certificates.subdomains)}"
        if certificates.status == "known"
        else "Certificate transparency unavailable",
    ]
    if dns.dmarc == "enforce":
        observations.append("DMARC enforcement is published")
    inconsistencies = []
    if intake.sends_external_email is False and (dns.spf != "absent" or dns.dmarc != "absent"):
        inconsistencies.append(
            "Intake says no external email, but the domain publishes email-authentication records"
        )
    return SecurityPostureSnapshot(
        observations=observations,
        prefills={
            "dmarc_enforced": dns.dmarc == "enforce",
            "observed_technologies": homepage.technologies,
        },
        inconsistencies=inconsistencies,
    )
