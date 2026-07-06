"""API tests for the omniagent-compatible backend (omni router).

Responses are raw (un-enveloped) camelCase payloads with numeric ids, matching
the frontend's generated client contract.

Run from the repo root:
    backend/.venv/Scripts/python.exe -m pytest tests/backend -v
"""


def create_case(client, service_id: int = 1) -> dict:
    response = client.post(
        "/api/cases",
        json={
            "serviceId": service_id,
            "applicantName": "Test Citizen",
            "applicantEmail": "test@demo.local",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_healthz(client):
    response = client.get("/api/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_services_raw_camelcase(client):
    response = client.get("/api/services")
    assert response.status_code == 200
    services = response.json()
    assert isinstance(services, list) and len(services) == 10
    first = services[0]
    assert first["id"] == 1
    assert "nameAr" in first and "nameFr" in first
    assert "processingDays" in first
    assert isinstance(first["requiredDocuments"], list)


def test_get_service_by_numeric_id(client):
    response = client.get("/api/services/2")
    assert response.status_code == 200
    assert response.json()["id"] == 2


def test_get_service_not_found(client):
    assert client.get("/api/services/999").status_code == 404


def test_signup_login_me_flow(client):
    signup = client.post(
        "/api/auth/signup",
        json={
            "fullName": "Test User",
            "email": "citizen1@demo.ma",
            "phone": "+212600000000",
            "password": "secret123",
        },
    )
    assert signup.status_code == 201, signup.text
    body = signup.json()
    assert body["token"]
    assert body["user"]["email"] == "citizen1@demo.ma"
    assert body["user"]["fullName"] == "Test User"
    assert body["user"]["isAdmin"] is False

    login = client.post(
        "/api/auth/login",
        json={"email": "citizen1@demo.ma", "password": "secret123"},
    )
    assert login.status_code == 200
    token = login.json()["token"]

    headers = {"Authorization": f"Bearer {token}"}
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "citizen1@demo.ma"

    updated = client.patch("/api/auth/me", headers=headers, json={"phone": "+212611111111"})
    assert updated.status_code == 200
    assert updated.json()["phone"] == "+212611111111"


def test_signup_duplicate_email(client):
    payload = {"fullName": "Dup", "email": "dup@demo.ma", "password": "secret123"}
    assert client.post("/api/auth/signup", json=payload).status_code == 201
    assert client.post("/api/auth/signup", json=payload).status_code == 409


def test_login_wrong_password(client):
    client.post(
        "/api/auth/signup",
        json={"fullName": "Pw", "email": "pw@demo.ma", "password": "secret123"},
    )
    response = client.post(
        "/api/auth/login", json={"email": "pw@demo.ma", "password": "nope"}
    )
    assert response.status_code == 401


def test_signup_short_password_rejected(client):
    response = client.post(
        "/api/auth/signup",
        json={"fullName": "Short", "email": "short@demo.ma", "password": "123"},
    )
    assert response.status_code == 422


def test_admin_login_success(client):
    response = client.post(
        "/api/admin/login",
        json={"email": "admin@demo.local", "password": "admin123"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["tokens"]["accessToken"]
    assert data["user"]["isAdmin"] is True


def test_admin_login_wrong_password(client):
    response = client.post(
        "/api/admin/login",
        json={"email": "admin@demo.local", "password": "nope"},
    )
    assert response.status_code == 401


def test_create_and_get_case(client):
    case = create_case(client)
    assert isinstance(case["id"], int)
    assert case["referenceNumber"].startswith("OMN-")
    assert case["serviceId"] == 1
    assert case["status"] == "submitted"
    assert case["service"]["id"] == 1

    fetched = client.get(f"/api/cases/{case['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == case["id"]


def test_create_case_unknown_service(client):
    response = client.post(
        "/api/cases",
        json={"serviceId": 999, "applicantName": "X", "applicantEmail": "x@y.z"},
    )
    assert response.status_code == 404


def test_list_cases(client):
    create_case(client)
    response = client.get("/api/cases")
    assert response.status_code == 200
    cases = response.json()
    assert isinstance(cases, list) and len(cases) >= 1
    assert all(isinstance(c["id"], int) for c in cases)


def test_patch_case_status(client):
    case = create_case(client)
    response = client.patch(
        f"/api/cases/{case['id']}",
        json={"status": "in_review", "notes": "under review"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "in_review"
    assert body["notes"] == "under review"


def test_case_timeline(client):
    case = create_case(client)
    client.patch(f"/api/cases/{case['id']}", json={"status": "approved"})
    response = client.get(f"/api/cases/{case['id']}/timeline")
    assert response.status_code == 200
    events = response.json()
    event_names = [e["event"] for e in events]
    assert "created" in event_names
    assert "status_changed" in event_names
    assert all("descriptionAr" in e and "descriptionFr" in e for e in events)


def test_case_messages_flow(client):
    case = create_case(client, service_id=2)  # birth certificate
    send = client.post(
        f"/api/cases/{case['id']}/messages",
        json={"content": "شنو الوثائق المطلوبة لعقد الازدياد؟", "language": "darija"},
    )
    assert send.status_code == 201
    assistant = send.json()
    assert assistant["role"] == "assistant"
    assert assistant["content"]

    history = client.get(f"/api/cases/{case['id']}/messages").json()
    roles = [m["role"] for m in history]
    assert "user" in roles and "assistant" in roles


def test_case_documents_empty(client):
    case = create_case(client)
    response = client.get(f"/api/cases/{case['id']}/documents")
    assert response.status_code == 200
    assert response.json() == []


def test_upload_document_flow(client):
    case = create_case(client)
    response = client.post(
        f"/api/cases/{case['id']}/documents",
        data={"docType": "national_id"},
        files={"file": ("cin.png", b"fake-png-bytes", "image/png")},
    )
    assert response.status_code == 201, response.text
    doc = response.json()
    assert doc["name"] == "cin.png"
    assert doc["fileType"] == "image/png"
    assert doc["fileSize"] == len(b"fake-png-bytes")
    assert doc["status"] == "pending"
    assert doc["caseId"] == case["id"]

    listing = client.get(f"/api/cases/{case['id']}/documents").json()
    assert len(listing) == 1
    assert listing[0]["name"] == "cin.png"

    timeline = client.get(f"/api/cases/{case['id']}/timeline").json()
    assert "uploaded" in [event["event"] for event in timeline]


def test_upload_document_rejects_bad_type(client):
    case = create_case(client)
    response = client.post(
        f"/api/cases/{case['id']}/documents",
        files={"file": ("virus.exe", b"MZ...", "application/x-msdownload")},
    )
    assert response.status_code == 415


def test_upload_document_rejects_oversized(client):
    case = create_case(client)
    oversized = b"x" * (10 * 1024 * 1024 + 1)
    response = client.post(
        f"/api/cases/{case['id']}/documents",
        files={"file": ("big.pdf", oversized, "application/pdf")},
    )
    assert response.status_code == 413


def test_upload_document_rejects_empty_file(client):
    case = create_case(client)
    response = client.post(
        f"/api/cases/{case['id']}/documents",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 400


def test_upload_document_sanitizes_filename(client):
    case = create_case(client)
    response = client.post(
        f"/api/cases/{case['id']}/documents",
        files={"file": ("../../etc/passwd.png", b"data", "image/png")},
    )
    assert response.status_code == 201
    assert "/" not in response.json()["name"]
    assert ".." not in response.json()["name"]


def test_standalone_chat(client):
    send = client.post(
        "/api/chat/messages",
        json={"content": "شنو الوثائق لشهادة السكنى؟", "language": "darija"},
    )
    assert send.status_code == 201
    msg = send.json()
    assert msg["role"] == "assistant"
    assert msg["caseId"] is None
    assert msg["content"]

    listing = client.get("/api/chat/messages")
    assert listing.status_code == 200
    assert len(listing.json()) >= 2


def test_dashboard_summary(client):
    create_case(client)
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    for key in (
        "totalCases",
        "activeCases",
        "pendingDocuments",
        "approvedCases",
        "avgProcessingDays",
        "recentCases",
        "casesByStatus",
    ):
        assert key in data
    assert data["totalCases"] >= 1


def test_admin_stats_requires_admin(client):
    assert client.get("/api/admin/stats").status_code == 403


def test_admin_stats_with_admin(client, admin_headers):
    create_case(client)
    response = client.get("/api/admin/stats", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["totalServices"] == 10
    assert data["totalCases"] >= 1
    assert isinstance(data["casesByService"], list)


def test_admin_cases_requires_admin(client):
    assert client.get("/api/admin/cases").status_code == 403


def test_admin_cases_with_admin(client, admin_headers):
    create_case(client)
    response = client.get("/api/admin/cases", headers=admin_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
