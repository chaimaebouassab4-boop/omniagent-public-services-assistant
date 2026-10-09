"""Tests for Feature 2: Structured Document OCR & Anomaly Detection."""

import io
import pytest
from PIL import Image, ImageDraw, ImageFont
from fastapi.testclient import TestClient
from main import app
from app.services import document_analyzer
from app.services.document_analyzer import (
    _heuristic_structured_extract,
    _normalized_image_variants,
    _correct_tesseract_orientation,
    _ocr_with_tesseract,
    extract_structured_metadata,
    LocalOcrResult,
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
    assert extracted.classification_source == "local_rules"
    assert extracted.classification_confidence >= 0.8
    assert extracted.field_metadata["national_id"]["source"] == "regex_local"
    assert extracted.field_metadata["birth_date"]["confidence"] >= 0.9
    assert extracted.extraction_confidence == extracted.confidence_score


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


def test_filename_alone_cannot_false_positive_as_cnie():
    extracted = _heuristic_structured_extract(
        "photographie sans texte administratif identifiable",
        "cin_cnie_identity_card.jpg",
        lang="fr",
    )
    assert extracted.document_type == "unknown"
    assert extracted.classification_confidence < 0.5
    assert extracted.cin_number is None


def test_arabic_cnie_labels_and_fields():
    text = (
        "المملكة المغربية\n"
        "البطاقة الوطنية للتعريف\n"
        "الاسم العائلي: العلوي\n"
        "الاسم الشخصي: أمينة\n"
        "تاريخ الازدياد: 03/08/1994\n"
        "العنوان: شارع محمد الخامس الرباط\n"
        "AB123456\n"
    )
    extracted = _heuristic_structured_extract(text, "scan.png", lang="arabic")
    assert extracted.document_type == "cin"
    assert extracted.cin_number == "AB123456"
    assert extracted.first_name == "أمينة"
    assert extracted.last_name == "العلوي"
    assert extracted.birth_date == "03/08/1994"
    assert "الرباط" in (extracted.address or "")


def test_low_contrast_small_image_gets_deterministic_normalized_variant():
    image = Image.new("RGB", (320, 180), color=(128, 128, 128))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    variants = _normalized_image_variants(buffer.getvalue())
    assert [name for name, _ in variants] == ["original", "normalized"]
    assert variants[0][1].size == (320, 180)
    assert min(variants[1][1].size) > min(variants[0][1].size)


def test_tesseract_orientation_correction_rotates_when_osd_is_confident():
    class FakeTesseract:
        @staticmethod
        def image_to_osd(image, config=""):
            return "Orientation in degrees: 90\nRotate: 90\nOrientation confidence: 9.5"

    image = Image.new("RGB", (120, 60), color="white")
    corrected = _correct_tesseract_orientation(image, FakeTesseract())
    assert corrected.size == (60, 120)


def test_clear_cnie_image_with_real_local_ocr_when_engine_is_installed():
    image = Image.new("RGB", (1400, 500), color="white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 52)
    draw.text((70, 70), "CARTE NATIONALE D'IDENTITE", fill="black", font=font)
    draw.text((70, 180), "CIN BK654321", fill="black", font=font)
    draw.text((70, 290), "NOM BENALI PRENOM AHMED", fill="black", font=font)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    ocr = _ocr_with_tesseract(buffer.getvalue())
    if ocr.status == "unavailable":
        pytest.skip("Tesseract executable/language packs are not installed on this host")
    assert ocr.status == "success"
    assert "BK654321" in ocr.text.replace(" ", "")


def test_local_ocr_and_rules_work_when_gemini_is_unavailable(monkeypatch):
    sample_text = (
        "ROYAUME DU MAROC\nCARTE NATIONALE D'IDENTITE\n"
        "CIN: BK654321\nNom: BENALI\nPrenom: AHMED\n"
        "Ne le: 15/05/1992\nAdresse: Casablanca\n"
    )
    monkeypatch.setattr(
        document_analyzer,
        "_local_text_extraction",
        lambda *_: (
            sample_text,
            1,
            LocalOcrResult(
                text=sample_text,
                confidence=0.88,
                backend="tesseract_normalized",
                status="success",
                languages=("ara", "fra", "eng"),
            ),
        ),
    )
    result = extract_structured_metadata(
        b"clear-cnie-image",
        "image/png",
        "upload.png",
        google_api_key="",
    )
    assert result.document_type == "cin"
    assert result.cin_number == "BK654321"
    assert result.ocr_backend == "tesseract_normalized"
    assert result.ocr_confidence == 0.88
    assert result.classification_source == "local_rules"


def test_gemini_vision_failure_does_not_trigger_second_provider_call(monkeypatch):
    monkeypatch.setattr(
        document_analyzer,
        "_local_text_extraction",
        lambda *_: ("", 1, LocalOcrResult(status="unavailable")),
    )
    monkeypatch.setattr(document_analyzer, "_ocr_with_gemini", lambda *_: "")

    def unexpected_generate(**kwargs):
        raise AssertionError("structured Gemini must not run after Vision is unavailable")

    monkeypatch.setattr(document_analyzer, "generate_text", unexpected_generate)
    result = extract_structured_metadata(
        b"low-quality-image",
        "image/jpeg",
        "upload.jpg",
        google_api_key="configured-but-unavailable",
    )
    assert result.document_type == "unknown"
    assert result.ocr_confidence == 0.0
    assert result.extraction_confidence < 0.2


def test_document_debug_traces_are_pii_safe(monkeypatch):
    pii_values = ["BK654321", "AHMED", "BENALI", "15/05/1992", "Casablanca"]
    sample_text = (
        "CARTE NATIONALE D'IDENTITE\nCIN: BK654321\n"
        "Nom: BENALI\nPrenom: AHMED\nNe le: 15/05/1992\nAdresse: Casablanca"
    )
    monkeypatch.setattr(
        document_analyzer,
        "_local_text_extraction",
        lambda *_: (
            sample_text,
            1,
            LocalOcrResult(text=sample_text, confidence=0.9, backend="tesseract", status="success"),
        ),
    )
    traces = []
    monkeypatch.setattr(
        document_analyzer,
        "development_trace",
        lambda section, **fields: traces.append((section, fields)),
    )
    extract_structured_metadata(b"image", "image/png", "AHMED_BK654321.png")
    rendered = repr(traces)
    assert {section for section, _ in traces} == {
        "DOCUMENT OCR",
        "DOCUMENT CLASSIFIER",
        "FIELD EXTRACTION",
        "DOCUMENT AI",
    }
    assert all(value not in rendered for value in pii_values)


def test_api_documents_analyze_extract(monkeypatch):
    """Test POST /api/documents/analyze-extract with sample PNG."""
    # Integration tests must exercise the deterministic fallback without
    # depending on a live Gemini account or network connectivity.
    monkeypatch.setattr("app.api.omni.settings.google_api_key", "")
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
    assert "ocr_confidence" in data
    assert "classification_confidence" in data
    assert "extraction_confidence" in data
    assert "field_metadata" in data
    assert "warnings" in data
