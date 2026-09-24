import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_devpulse.db")
os.environ.setdefault("JWT_SECRET", "test-secret-for-devpulse")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
