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


def test_upload_cin_flow(client):
    signup = client.post(
        "/api/auth/signup",
        json={"fullName": "Cin User", "email": "cin@demo.ma", "password": "secret123"},
    )
    token = signup.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/users/me/documents/cin",
        headers=headers,
        files={"file": ("ma_cin.png", b"png-bytes", "image/png")},
    )
    assert response.status_code == 201, response.text
    assert response.json()["cinFileName"] == "ma_cin.png"

    me = client.get("/api/auth/me", headers=headers).json()
    assert me["cinFileName"] == "ma_cin.png"

    preview = client.get("/api/users/me/documents/cin", headers=headers)
    assert preview.status_code == 200
    assert preview.content == b"png-bytes"
    assert preview.headers["content-type"].startswith("image/png")
    assert preview.headers["content-disposition"].startswith("inline;")

    # JPEG is not allowed for the CIN (PNG/PDF only)
    rejected = client.post(
        "/api/users/me/documents/cin",
        headers=headers,
        files={"file": ("cin.jpg", b"jpg", "image/jpeg")},
    )
    assert rejected.status_code == 415


def test_upload_personal_document_flow(client):
    signup = client.post(
        "/api/auth/signup",
        json={"fullName": "Doc User", "email": "docs@demo.ma", "password": "secret123"},
    )
    token = signup.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/users/me/documents/personal",
        headers=headers,
        files={"file": ("attestation.pdf", b"%PDF-fake", "application/pdf")},
    )
    assert response.status_code == 201, response.text
    docs = response.json()["personalDocuments"]
    assert len(docs) == 1
    assert docs[0]["name"] == "attestation.pdf"
    assert docs[0]["size"] == len(b"%PDF-fake")
    assert "path" not in docs[0], "server paths must not be exposed"

    second = client.post(
        "/api/users/me/documents/personal",
        headers=headers,
        files={"file": ("releve.png", b"png", "image/png")},
    )
    assert len(second.json()["personalDocuments"]) == 2


def test_chat_document_upload(client):
    response = client.post(
        "/api/chat/documents",
        data={"language": "fr"},
        files={"file": ("dossier.pdf", b"%PDF-not-really", "application/pdf")},
    )
    assert response.status_code == 201, response.text
    ack = response.json()
    assert ack["role"] == "assistant"
    assert "dossier.pdf" in ack["content"]

    listing = client.get("/api/chat/messages").json()
    contents = [m["content"] for m in listing]
    assert any(c.startswith("[Document] dossier.pdf") for c in contents)
    # The hidden extraction context must never appear in the thread
    assert all("document_context" not in m["role"] for m in listing)


def make_citizen(client, email: str) -> dict:
    response = client.post(
        "/api/auth/signup",
        json={"fullName": "Chat User", "email": email, "password": "secret123"},
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_chat_history_is_isolated_per_user(client):
    headers_a = make_citizen(client, "chat_a@demo.ma")
    headers_b = make_citizen(client, "chat_b@demo.ma")

    send = client.post(
        "/api/chat/messages",
        headers=headers_a,
        json={"content": "شنو الوثائق لشهادة السكنى؟", "language": "darija"},
    )
    assert send.status_code == 201

    history_a = client.get("/api/chat/messages", headers=headers_a).json()
    assert len(history_a) == 2  # user question + assistant answer

    history_b = client.get("/api/chat/messages", headers=headers_b).json()
    assert history_b == [], "user B must never see user A's messages"


def test_clear_chat_history_only_affects_current_user(client):
    headers_a = make_citizen(client, "clear_a@demo.ma")
    headers_b = make_citizen(client, "clear_b@demo.ma")

    client.post("/api/chat/messages", headers=headers_a, json={"content": "سلام", "language": "darija"})
    client.post("/api/chat/messages", headers=headers_b, json={"content": "سلام", "language": "darija"})

    cleared = client.delete("/api/chat/messages", headers=headers_a)
    assert cleared.status_code == 200
    assert cleared.json()["deleted"] == 2

    assert client.get("/api/chat/messages", headers=headers_a).json() == []
    assert len(client.get("/api/chat/messages", headers=headers_b).json()) == 2


def test_chat_sessions_preserve_previous_conversations(client):
    headers = make_citizen(client, "sessions@demo.ma")

    first = "conversation-one"
    second = "conversation-two"
    client.post(
        "/api/chat/messages",
        headers=headers,
        json={"content": "Premier sujet", "language": "fr", "sessionId": first},
    )
    client.post(
        "/api/chat/messages",
        headers=headers,
        json={"content": "Deuxième sujet", "language": "fr", "sessionId": second},
    )

    sessions = client.get("/api/chat/sessions", headers=headers).json()
    assert {item["id"] for item in sessions} == {first, second}
    assert next(item for item in sessions if item["id"] == first)["title"] == "Premier sujet"

    first_history = client.get(
        "/api/chat/messages", headers=headers, params={"sessionId": first}
    ).json()
    second_history = client.get(
        "/api/chat/messages", headers=headers, params={"sessionId": second}
    ).json()
    assert len(first_history) == 2
    assert len(second_history) == 2
    assert first_history[0]["content"] == "Premier sujet"
    assert second_history[0]["content"] == "Deuxième sujet"


def test_chat_document_history_scoped_to_user(client):
    headers = make_citizen(client, "chat_doc@demo.ma")
    response = client.post(
        "/api/chat/documents",
        headers=headers,
        files={"file": ("piece.png", b"png-bytes", "image/png")},
    )
    assert response.status_code == 201

    history = client.get("/api/chat/messages", headers=headers).json()
    assert any(m["content"].startswith("[Document] piece.png") for m in history)

    other = make_citizen(client, "chat_doc_other@demo.ma")
    assert client.get("/api/chat/messages", headers=other).json() == []


def test_chat_document_rejects_bad_type(client):
    response = client.post(
        "/api/chat/documents",
        files={"file": ("script.exe", b"MZ", "application/x-msdownload")},
    )
    assert response.status_code == 415


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
