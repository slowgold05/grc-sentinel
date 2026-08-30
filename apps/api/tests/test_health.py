from fastapi.testclient import TestClient

from ruleset.main import app


def test_health() -> None:
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/audit/share/invalid").status_code == 404
