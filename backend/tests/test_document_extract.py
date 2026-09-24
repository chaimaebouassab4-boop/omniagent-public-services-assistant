"""Tests for Feature 2: Structured Document OCR & Anomaly Detection."""

import io
from fastapi.testclient import TestClient
from main import app
from app.services.document_analyzer import (
    _heuristic_structured_extract,
    DOCUMENT_TYPE_LABELS,
)

client = TestClient(app)


def test_heuristic_cin_extraction():
    """Verify Moroccan CIN text extraction parses fields correctly."""
    sample_text = (
        "ROYAUME DU MAROC\n"
        "CARTE NATIONALE D'IDENTITE\n"
        "CIN: BK654321\n"
        "Nom: BENALI\n"
        "Prenom: AHMED\n"
        "Ne le: 15/05/1992\n"
        "Adresse: 45 Boulevard d'Anfa Casablanca\n"
        "Valable jusqu'au: 10/12/2030\n"
    )

    extracted = _heuristic_structured_extract(sample_text, "cin.pdf", lang="fr")
    assert extracted.document_type == "cin"
    assert extracted.cin_number == "BK654321"
    assert extracted.first_name == "Ahmed"
    assert extracted.last_name == "Benali"
    assert extracted.full_name == "Ahmed Benali"
    assert extracted.birth_date == "15/05/1992"
    assert "45 Boulevard d'Anfa Casablanca" in (extracted.address or "")
    assert extracted.is_valid is True
    assert extracted.is_expired is False


def test_heuristic_expired_document_anomaly():
    """Verify anomaly detection flags expired document."""
    sample_text = (
        "CARTE NATIONALE\n"
        "BK123456\n"
        "Nom: ALAMI\n"
        "Prenom: FATIMA\n"
        "Valable jusqu'au: 01/01/2020\n"
    )

    extracted = _heuristic_structured_extract(sample_text, "cin.pdf", lang="fr")
    assert extracted.is_expired is True
    assert extracted.is_valid is False
    assert any("expiré" in w.lower() for w in extracted.warnings)


def test_heuristic_irrelevant_document_anomaly():
    """Verify irrelevant document (e.g. random image) is flagged."""
    sample_text = "Hello world selfie photo dog"

    extracted = _heuristic_structured_extract(sample_text, "photo.jpg", lang="fr")
    assert extracted.is_relevant is False or extracted.document_type in ("irrelevant", "other")


def test_api_documents_analyze_extract():
    """Test POST /api/documents/analyze-extract with sample PNG."""
    # Create a tiny 1x1 dummy PNG
    tiny_png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    response = client.post(
        "/api/documents/analyze-extract",
        files={"file": ("test_cin.png", io.BytesIO(tiny_png), "image/png")},
        data={"language": "fr"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "document_type" in data
    assert "document_type_label" in data
    assert "confidence_score" in data
    assert "warnings" in data
