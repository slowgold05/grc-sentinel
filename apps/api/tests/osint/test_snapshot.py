from ruleset.intake.models import CompanyIntake
from ruleset.osint.certificate_transparency import CertificateFootprint
from ruleset.osint.dns_posture import DnsPosture
from ruleset.osint.homepage import HomepagePosture
from ruleset.osint.security_headers import HeaderPosture
from ruleset.osint.snapshot import build_snapshot


def test_snapshot_flags_email_claim_inconsistency() -> None:
    snapshot = build_snapshot(
        CompanyIntake(
            company_name="Example",
            domain="example.com",
            employee_count=10,
            sends_external_email=False,
        ),
        DnsPosture(domain="example.com", spf="hardfail", dmarc="enforce", dkim="unknown"),
        CertificateFootprint(status="known", subdomains=["www.example.com"]),
        HomepagePosture(
            headers=HeaderPosture(present=[], missing=[], grade="F"),
            technologies=["Cloudflare"],
        ),
    )
    assert snapshot.prefills["dmarc_enforced"] is True
    assert snapshot.inconsistencies
