from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test GET /api/health endpoint returns 200 and healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Minni - AI Safety Assistant"
    assert "version" in data
    assert "timestamp" in data


def test_root_endpoint():
    """Test root endpoint redirect/welcome dictionary."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["docs"] == "/docs"
    assert data["health"] == "/api/health"
    assert data["chat_endpoint"] == "/api/chat"
