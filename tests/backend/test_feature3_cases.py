"""Feature 3 end-to-end case lifecycle, visibility, and receipt checks."""

from io import BytesIO

from pypdf import PdfReader

from app.services.case_notifications import notification_draft
from app.services.mock_citizens import generate_mock_citizens


def _create(client, *, submit=True):
    response = client.post("/api/cases", json={
        "serviceId": 1,
        "applicantName": "Test Citizen",
        "applicantEmail": "citizen@example.test",
        "submit": submit,
    })
    assert response.status_code == 201, response.text
    return response.json()


def test_draft_submission_and_step_timestamps(client, admin_headers):
    case = _create(client, submit=False)
    assert case["status"] == "DRAFT"
    assert case["trackingCode"].startswith("MA-")
    assert client.get(f"/api/cases/{case['id']}/receipt").status_code == 409

    submitted = client.patch(f"/api/cases/{case['id']}", json={"status": "SUBMITTED"})
    assert submitted.status_code == 200, submitted.text
    assert [entry["status"] for entry in submitted.json()["statusHistory"]] == ["DRAFT", "SUBMITTED"]

    skipped = client.patch(f"/api/admin/cases/{case['id']}", headers=admin_headers, json={"status": "READY_FOR_PICKUP"})
    assert skipped.status_code == 409

    for step in ("UNDER_REVIEW", "DOCS_APPROVED", "READY_FOR_PICKUP"):
        response = client.patch(f"/api/admin/cases/{case['id']}", headers=admin_headers, json={"status": step})
        assert response.status_code == 200, response.text
        assert response.json()["status"] == step

    timeline = client.get(f"/api/cases/{case['id']}/timeline").json()
    assert [event["status"] for event in timeline if event["event"] == "status_changed"] == [
        "SUBMITTED", "UNDER_REVIEW", "DOCS_APPROVED", "READY_FOR_PICKUP",
    ]
    assert client.patch(f"/api/admin/cases/{case['id']}", headers=admin_headers, json={"status": "UNDER_REVIEW"}).status_code == 409


def test_missing_document_action_and_notification_draft(client, admin_headers):
    case = _create(client)
    client.patch(f"/api/admin/cases/{case['id']}", headers=admin_headers, json={"status": "UNDER_REVIEW"})
    response = client.patch(f"/api/admin/cases/{case['id']}", headers=admin_headers, json={"nextAction": "Facture d'électricité"})
    assert response.status_code == 200, response.text
    assert "Facture" in response.json()["nextAction"]
    assert client.patch(f"/api/cases/{case['id']}", json={"nextAction": "Forged"}).status_code == 403
    timeline = client.get(f"/api/cases/{case['id']}/timeline").json()
    assert timeline[-1]["event"] == "action_required"
    assert "Facture" in timeline[-1]["notificationDraft"]["fr"]
    uploaded = client.post(
        f"/api/cases/{case['id']}/documents",
        files={"file": ("facture.pdf", b"%PDF-1.4 mock", "application/pdf")},
    )
    assert uploaded.status_code == 201, uploaded.text
    refreshed = client.get(f"/api/cases/{case['id']}").json()
    assert "Facture" not in refreshed["nextAction"]
    assert client.get(f"/api/cases/{case['id']}/timeline").json()[-1]["event"] == "action_resolved"

    note = notification_draft("UNDER_REVIEW", case["trackingCode"], missing_document="Facture")
    assert case["trackingCode"] in note["fr"] and case["trackingCode"] in note["darija"]


def test_receipt_pdf_and_case_ownership(client):
    case = _create(client)
    receipt = client.get(f"/api/cases/{case['id']}/receipt")
    assert receipt.status_code == 200, receipt.text
    assert receipt.headers["content-type"].startswith("application/pdf")
    assert receipt.content.startswith(b"%PDF")
    text = PdfReader(BytesIO(receipt.content)).pages[0].extract_text()
    assert case["trackingCode"] in text
    assert "NON OFFICIEL" in text

    signup = client.post("/api/auth/signup", json={
        "fullName": "Other User", "email": "other-feature3@example.test", "password": "secret123",
    })
    token = signup.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    for path in (f"/api/cases/{case['id']}", f"/api/cases/{case['id']}/timeline", f"/api/cases/{case['id']}/receipt"):
        assert client.get(path, headers=headers).status_code == 403


def test_mock_profiles_are_repeatable_and_synthetic():
    profiles = generate_mock_citizens(20, seed=42)
    assert profiles == generate_mock_citizens(20, seed=42)
    assert len({profile["cin"] for profile in profiles}) == 20
    assert all(profile["synthetic"] and profile["city"] in {"Casablanca", "Rabat"} for profile in profiles)


def test_sample_verification_is_explicitly_mock(client):
    found = client.post("/api/verify/cin", json={"value": "BK654321"})
    assert found.status_code == 200
    assert found.json()["data"]["valid"] is True
    assert found.json()["data"]["synthetic"] is True
    missing = client.post("/api/verify/cnss", json={"value": "000000000"})
    assert missing.status_code == 200
    assert missing.json()["data"]["valid"] is False
