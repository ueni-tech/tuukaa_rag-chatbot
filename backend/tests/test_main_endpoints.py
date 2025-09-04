from datetime import datetime
from fastapi.testclient import TestClient


def test_root_health(client: TestClient):
    r = client.get("/")
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        data = r.json()
        assert data["status"] == "healthy"
        assert isinstance(data["version"], str)
        assert isinstance(data["timestamp"], str)
        assert "T" in data["timestamp"]


def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        data = r.json()
        assert data["status"] in {"healthy", "degraded"}
        assert isinstance(data["version"], str)
        assert isinstance(data["timestamp"], str)


pass
