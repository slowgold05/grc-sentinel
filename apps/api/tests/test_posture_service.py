from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import create_engine, text

from ruleset.config import settings
from ruleset.osint.certificate_transparency import CertificateFootprint
from ruleset.osint.dns_posture import DnsPosture
from ruleset.osint.homepage import HomepagePosture
from ruleset.osint.security_headers import HeaderPosture
from ruleset.posture_service import collect_posture


def test_collects_and_caches_passive_posture() -> None:
    engine = create_engine(str(settings.database_url))
    org_id, engagement_id = uuid4(), uuid4()
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        connection.execute(text("INSERT INTO orgs (id, name) VALUES (:id, 'posture test')"), {"id": org_id})
        connection.execute(
            text(
                "INSERT INTO engagements (id, org_id, company, expires_at) VALUES "
                "(:id, :org, :company, :expires)"
            ),
            {
                "id": engagement_id,
                "org": org_id,
                "company": '{"company_name":"Example","domain":"example.com",'
                '"employee_count":10,"sends_external_email":false}',
                "expires": datetime.now(UTC) + timedelta(days=1),
            },
        )
    try:
        snapshot = collect_posture(
            engine,
            org_id,
            engagement_id,
            dns_check=lambda domain: DnsPosture(
                domain=domain, spf="hardfail", dmarc="enforce", dkim="unknown"
            ),
            certificate_check=lambda _: CertificateFootprint(
                status="known", subdomains=["www.example.com"]
            ),
            homepage_check=lambda _: HomepagePosture(
                headers=HeaderPosture(present=["HSTS"], missing=[], grade="B"),
                technologies=["Cloudflare"],
            ),
        )
        assert snapshot.prefills["dmarc_enforced"] is True
        assert snapshot.inconsistencies
    finally:
        with engine.begin() as connection:
            connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
