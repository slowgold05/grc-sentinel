from base64 import urlsafe_b64encode
from datetime import UTC, datetime, timedelta
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import text

from ruleset.auth import TenantIdentity, require_tenant
from ruleset.config import settings
from ruleset.database import engine
from ruleset.main import app


def test_upload_api_validates_parses_and_encrypts_docx() -> None:
    org_id, engagement_id = uuid4(), uuid4()
    payload = BytesIO()
    with ZipFile(payload, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body><w:p><w:r><w:t>Access policy</w:t></w:r></w:p></w:body></w:document>",
        )
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        connection.execute(text("INSERT INTO orgs (id, name) VALUES (:id, 'upload api')"), {"id": org_id})
        connection.execute(
            text(
                "INSERT INTO engagements (id, org_id, company, expires_at) "
                "VALUES (:id, :org, '{}', :expires)"
            ),
            {"id": engagement_id, "org": org_id, "expires": datetime.now(UTC) + timedelta(days=1)},
        )
    app.dependency_overrides[require_tenant] = lambda: TenantIdentity(
        org_id=org_id, user_id="user_test", provider_org_id="org_test"
    )
    original_key = settings.upload_master_key_base64
    settings.upload_master_key_base64 = SecretStr(
        urlsafe_b64encode(AESGCM.generate_key(bit_length=256)).decode()
    )
    try:
        response = TestClient(app).post(
            f"/api/engagements/{engagement_id}/uploads",
            headers={"X-Filename": "policy.docx", "Content-Type": "application/octet-stream"},
            content=payload.getvalue(),
        )
        assert response.status_code == 201
        assert response.json()["sections"] == 1
    finally:
        settings.upload_master_key_base64 = original_key
        app.dependency_overrides.clear()
        with engine.begin() as connection:
            connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
            connection.execute(text("DELETE FROM orgs WHERE id = :id"), {"id": org_id})
