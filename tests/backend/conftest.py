import os
import sys
import uuid
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import tempfile

# Set isolation before pytest imports test modules that may instantiate Settings.
TEST_RUN_DIR = Path(tempfile.gettempdir()) / "omni-pytest-tmp" / uuid.uuid4().hex
TEST_RUN_DIR.mkdir(parents=True, exist_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{(TEST_RUN_DIR / 'test.db').as_posix()}"
os.environ["UPLOAD_ROOT"] = str(TEST_RUN_DIR / "uploads")


@pytest.fixture(scope="session")
def client(tmp_path_factory):
    """TestClient backed by a throwaway SQLite database."""
    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def admin_headers(client):
    """Authorization header for the seeded admin account."""
    response = client.post(
        "/api/admin/login",
        json={"email": "admin@demo.local", "password": "admin123"}
    )
    assert response.status_code == 200, response.text
    token = response.json()["data"]["tokens"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}
