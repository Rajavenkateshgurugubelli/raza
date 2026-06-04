import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "agent" in data
    assert "version" in data

def test_system_providers():
    response = client.get("/api/system/providers")
    assert response.status_code == 200
    data = response.json()
    assert "available" in data
    assert "provider_order" in data

def test_system_tools():
    response = client.get("/api/system/tools")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_system_status():
    response = client.get("/api/system/status")
    assert response.status_code == 200
    data = response.json()
    assert "agent" in data
    assert "version" in data
    assert "memory" in data
    assert "tools" in data
