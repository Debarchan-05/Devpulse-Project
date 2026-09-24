import os
import pathlib

# IMPORTANT: these env vars must be set *before* anything under app/ is
# imported anywhere in the test session, because app/core/config.py reads
# them once at import time. Using SQLite here (instead of a real MySQL
# server) keeps the test suite fast and dependency-free, while still
# exercising real SQL -- including the window-function leaderboard query,
# since SQLite 3.25+ (bundled with modern Python) supports ROW_NUMBER()
# and RANK() too.
TEST_DB_PATH = pathlib.Path(__file__).parent / "test_devpulse.db"
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DB_PATH}")
os.environ.setdefault("JWT_SECRET", "test-secret-for-devpulse")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault("SYNC_COOLDOWN_SECONDS", "0")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


def register_and_login(client: TestClient, email: str) -> str:
    """Helper used by multiple test files: creates a user and returns a
    bearer token for it."""
    client.post(
        "/api/v1/auth/register",
        json={"name": "Test User", "email": email, "password": "password123"},
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "password123"},
    )
    return response.json()["access_token"]
