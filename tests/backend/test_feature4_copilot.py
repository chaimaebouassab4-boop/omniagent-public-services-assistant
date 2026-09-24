"""Feature 4 copilot, quick actions, and repeatable presentation personas."""


def _activate(client, admin_headers, persona: str):
    response = client.post(f"/api/admin/demo-personas/{persona}", headers=admin_headers)
    assert response.status_code == 200, response.text
    return response.json()


def test_amines_case_is_grounded_and_approvable(client, admin_headers):
    demo = _activate(client, admin_headers, "amine")
    case_id = demo["case"]["id"]
    response = client.get(f"/api/admin/cases/{case_id}/ai-summary", headers=admin_headers)
    assert response.status_code == 200, response.text
    summary = response.json()

    assert summary["documentsCheck"]["present"] == 3
    assert summary["documentsCheck"]["required"] == 3
    assert summary["discrepancyChecks"][0]["status"] == "MATCH"
    assert summary["recommendation"]["action"] == "APPROVE"
    assert summary["decisionSupportOnly"] is True

    approved = client.post(f"/api/admin/cases/{case_id}/actions/approve", headers=admin_headers)
    assert approved.status_code == 200, approved.text
    assert approved.json()["case"]["status"] == "DOCS_APPROVED"
    preview = approved.json()["notificationPreview"]
    assert preview["channel"] == "SMS"
    assert demo["case"]["trackingCode"] in preview["fr"]
    assert demo["case"]["trackingCode"] in preview["darija"]


def test_birth_case_skips_irrelevant_address_comparison(client, admin_headers):
    demo = _activate(client, admin_headers, "fatima")
    summary = demo["aiSummary"]
    assert demo["persona"]["language"] == "fr"
    assert summary["documentsCheck"]["present"] == summary["documentsCheck"]["required"] == 3
    assert summary["discrepancyChecks"][0]["status"] == "NOT_APPLICABLE"
    assert summary["recommendation"]["action"] == "APPROVE"


def test_unreadable_document_prefills_bilingual_change_request(client, admin_headers):
    demo = _activate(client, admin_headers, "youssef")
    case_id = demo["case"]["id"]
    summary = demo["aiSummary"]
    assert summary["recommendation"]["action"] == "REQUEST_CHANGES"
    assert any(item["status"] == "UNREADABLE" for item in summary["documentsCheck"]["items"])

    rejected_approval = client.post(f"/api/admin/cases/{case_id}/actions/approve", headers=admin_headers)
    assert rejected_approval.status_code == 409

    requested = client.post(
        f"/api/admin/cases/{case_id}/actions/request-changes",
        headers=admin_headers,
        json={
            "reason": "Document illisible",
            "messageFr": "Merci de remplacer votre CIN illisible.",
            "messageDarija": "عافاك بدل البطاقة الوطنية اللي ما بايناش.",
        },
    )
    assert requested.status_code == 200, requested.text
    assert requested.json()["case"]["status"] == "UNDER_REVIEW"
    assert requested.json()["notificationPreview"]["fr"].startswith("Merci")
    assert requested.json()["notificationPreview"]["darija"].startswith("عافاك")


def test_admin_copilot_is_protected_and_personas_are_whitelisted(client, admin_headers):
    demo = _activate(client, admin_headers, "amine")
    case_id = demo["case"]["id"]
    assert client.get(f"/api/admin/cases/{case_id}/ai-summary").status_code == 403
    assert client.post("/api/admin/demo-personas/not-a-persona", headers=admin_headers).status_code == 404
