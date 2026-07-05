import os
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture(scope="session")
def client(tmp_path_factory):
    """TestClient backed by a throwaway SQLite database."""
    tmp_dir = tmp_path_factory.mktemp("api")
    os.environ["DATABASE_URL"] = f"sqlite:///{(tmp_dir / 'test.db').as_posix()}"
    os.environ["UPLOAD_ROOT"] = str(tmp_dir / "uploads")

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
