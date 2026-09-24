"""Evidence-grounded civil servant copilot for administrative case review."""

from __future__ import annotations

import re
import unicodedata
from datetime import UTC, datetime
from typing import Any

from app.services.case_notifications import notification_draft
from app.services.case_lifecycle import tracking_code


COPILOT_PROMPT_TEMPLATE = """You are the Civil Servant Copilot for Moroccan public services.
Compare one citizen case only against the official requirements supplied in the input.
Use exclusively the uploaded document metadata and OCR evidence supplied in the input.
Return strict JSON with: executiveSummary, documentsCheck, discrepancyChecks,
recommendation, reasons, and notificationDraft. Never invent a present document,
address match, identity match, validity result, or registry verification. If evidence is
missing or unreadable, say NOT_CHECKED and recommend REQUEST_CHANGES. The final decision
belongs to the civil servant; your output is decision support, not an official decision.
"""


DOCUMENT_LABELS: dict[str, dict[str, str]] = {
    "national_id": {"fr": "Carte nationale d'identité", "ar": "البطاقة الوطنية"},
    "proof_of_residence": {"fr": "Justificatif de domicile", "ar": "إثبات السكن"},
    "address_confirmation": {"fr": "Confirmation d'adresse", "ar": "تأكيد العنوان"},
    "parent_id": {"fr": "CIN du parent", "ar": "بطاقة تعريف أحد الوالدين"},
    "marriage_certificate": {"fr": "Acte de mariage", "ar": "عقد الزواج"},
    "hospital_record": {"fr": "Déclaration de naissance", "ar": "تصريح الولادة"},
    "both_ids": {"fr": "CIN des deux époux", "ar": "بطاقتا تعريف الزوجين"},
    "birth_certificates": {"fr": "Actes de naissance", "ar": "عقود الازدياد"},
    "witness_documents": {"fr": "Pièces des témoins", "ar": "وثائق الشهود"},
    "declarant_id": {"fr": "CIN du déclarant", "ar": "بطاقة تعريف المصرح"},
    "medical_death_notice": {"fr": "Constat médical de décès", "ar": "الشهادة الطبية للوفاة"},
    "family_book": {"fr": "Livret de famille", "ar": "الدفتر العائلي"},
    "residence_proof": {"fr": "Justificatif de résidence", "ar": "إثبات الإقامة"},
    "birth_certificate": {"fr": "Acte de naissance", "ar": "عقد الازدياد"},
    "witness_declaration": {"fr": "Déclaration des témoins", "ar": "تصريح الشهود"},
    "request_form": {"fr": "Formulaire de demande", "ar": "استمارة الطلب"},
    "supporting_documents": {"fr": "Pièces justificatives", "ar": "الوثائق الداعمة"},
    "photos": {"fr": "Photos d'identité", "ar": "الصور الشخصية"},
}

DOCUMENT_ALIASES: dict[str, tuple[str, ...]] = {
    "national_id": ("national id", "identity", "cin", "cnie", "carte nationale", "identite"),
    "proof_of_residence": ("proof of residence", "domicile", "facture", "electricite", "water", "eau", "residence"),
    "address_confirmation": ("address confirmation", "adresse", "address", "attestation hebergement", "confirmation"),
    "parent_id": ("parent id", "cin parent", "cnie parent"),
    "marriage_certificate": ("marriage", "mariage", "زواج"),
    "hospital_record": ("hospital", "hopital", "naissance", "birth declaration"),
    "both_ids": ("both ids", "cin epoux", "identites"),
    "birth_certificates": ("birth certificates", "actes naissance", "ازدياد"),
    "witness_documents": ("witness", "temoin", "شهود"),
    "declarant_id": ("declarant", "cin declarant"),
    "medical_death_notice": ("death notice", "deces", "medical", "وفاة"),
    "family_book": ("family book", "livret famille", "دفتر عائلي"),
    "residence_proof": ("residence proof", "domicile", "facture", "residence"),
    "birth_certificate": ("birth certificate", "acte naissance", "ازدياد"),
    "witness_declaration": ("witness declaration", "declaration temoin", "شهود"),
    "request_form": ("request form", "formulaire", "طلب"),
    "supporting_documents": ("supporting", "justificatif", "preuve"),
    "photos": ("photo", "photos"),
}


def _normalize(value: str | None) -> str:
    raw = unicodedata.normalize("NFKD", value or "")
    raw = "".join(char for char in raw if not unicodedata.combining(char))
    return " ".join(re.findall(r"[\w]+", raw.lower(), flags=re.UNICODE))


def _document_score(document: Any, requirement: str) -> int:
    doc_type = _normalize(document.doc_type)
    haystack = _normalize(f"{document.doc_type} {document.file_name} {document.ocr_text or ''}")
    if doc_type == _normalize(requirement):
        return 100
    score = 0
    for alias in DOCUMENT_ALIASES.get(requirement, (requirement.replace("_", " "),)):
        normalized = _normalize(alias)
        if normalized and normalized in haystack:
            score = max(score, 20 + len(normalized))
    return score


def _match_documents(required: list[str], documents: list[Any]) -> list[dict[str, Any]]:
    unused = set(range(len(documents)))
    checks: list[dict[str, Any]] = []
    for requirement in required:
        candidates = sorted(
            ((index, _document_score(documents[index], requirement)) for index in unused),
            key=lambda item: item[1],
            reverse=True,
        )
        match_index = candidates[0][0] if candidates and candidates[0][1] > 0 else None
        document = documents[match_index] if match_index is not None else None
        if match_index is not None:
            unused.remove(match_index)
        unreadable = bool(document and (
            document.validation_status == "rejected"
            or any(word in _normalize(document.ocr_text) for word in ("unreadable", "illisible", "غير مقروء"))
        ))
        status = "UNREADABLE" if unreadable else "PRESENT" if document else "MISSING"
        labels = DOCUMENT_LABELS.get(requirement, {
            "fr": requirement.replace("_", " ").title(),
            "ar": requirement.replace("_", " "),
        })
        checks.append({
            "requirement": requirement,
            "labelFr": labels["fr"],
            "labelAr": labels["ar"],
            "status": status,
            "documentId": document.id if document else None,
            "fileName": document.file_name if document else None,
            "validationStatus": document.validation_status if document else None,
        })
    return checks


def _extract_address(text: str | None) -> str | None:
    if not text:
        return None
    for line in text.splitlines():
        match = re.search(r"(?:address|adresse|العنوان)\s*[:\-]\s*(.+)", line, flags=re.IGNORECASE)
        if match and match.group(1).strip():
            return match.group(1).strip()
    return None


def _address_check(checks: list[dict[str, Any]], documents: list[Any]) -> dict[str, str]:
    address_requirements = {"proof_of_residence", "residence_proof", "address_confirmation"}
    if not any(item["requirement"] in address_requirements for item in checks):
        return {
            "field": "address",
            "status": "NOT_APPLICABLE",
            "detailFr": "Aucun contrôle d'adresse n'est requis pour ce service.",
            "detailAr": "هاد الخدمة ما كتطلبش التحقق من العنوان.",
        }
    by_id = {str(document.id): document for document in documents}
    identity_check = next((item for item in checks if item["requirement"] in {"national_id", "parent_id"}), None)
    address_check = next((item for item in checks if item["requirement"] in address_requirements), None)
    identity_doc = by_id.get(str(identity_check.get("documentId"))) if identity_check else None
    address_doc = by_id.get(str(address_check.get("documentId"))) if address_check else None
    identity_address = _extract_address(identity_doc.ocr_text if identity_doc else None)
    proof_address = _extract_address(address_doc.ocr_text if address_doc else None)
    if not identity_address or not proof_address:
        return {
            "field": "address",
            "status": "NOT_CHECKED",
            "detailFr": "Comparaison impossible : adresse OCR absente d'au moins une pièce.",
            "detailAr": "تعذرت المقارنة: عنوان OCR ناقص في وثيقة واحدة على الأقل.",
        }
    left, right = _normalize(identity_address), _normalize(proof_address)
    left_tokens, right_tokens = set(left.split()), set(right.split())
    overlap = len(left_tokens & right_tokens) / max(1, len(left_tokens | right_tokens))
    matches = left == right or left in right or right in left or overlap >= 0.65
    return {
        "field": "address",
        "status": "MATCH" if matches else "MISMATCH",
        "detailFr": "L'adresse du justificatif correspond à celle de la CIN." if matches else "L'adresse du justificatif ne correspond pas à celle de la CIN.",
        "detailAr": "العنوان فالإثبات مطابق للعنوان فالبطاقة الوطنية." if matches else "العنوان فالإثبات ما مطابقش للعنوان فالبطاقة الوطنية.",
    }


def evaluate_case(case: Any) -> dict[str, Any]:
    required = list(case.service.required_documents or []) if case.service else []
    documents = list(case.documents or [])
    checks = _match_documents(required, documents)
    present = sum(item["status"] == "PRESENT" for item in checks)
    missing = [item for item in checks if item["status"] == "MISSING"]
    unreadable = [item for item in checks if item["status"] == "UNREADABLE"]
    discrepancies = [_address_check(checks, documents)]
    has_mismatch = any(item["status"] == "MISMATCH" for item in discrepancies)
    has_unverified_discrepancy = any(item["status"] == "NOT_CHECKED" for item in discrepancies)
    recommendation = "APPROVE" if not missing and not unreadable and not has_mismatch and not has_unverified_discrepancy else "REQUEST_CHANGES"

    if missing:
        names_fr = ", ".join(item["labelFr"] for item in missing)
        names_ar = "، ".join(item["labelAr"] for item in missing)
        reason_fr = f"Pièces manquantes : {names_fr}."
        reason_ar = f"الوثائق الناقصة: {names_ar}."
    elif unreadable:
        names_fr = ", ".join(item["labelFr"] for item in unreadable)
        names_ar = "، ".join(item["labelAr"] for item in unreadable)
        reason_fr = f"Pièces illisibles ou rejetées : {names_fr}."
        reason_ar = f"وثائق غير مقروءة أو مرفوضة: {names_ar}."
    elif has_mismatch:
        reason_fr = "Une incohérence d'adresse doit être corrigée."
        reason_ar = "خاص تصحيح الاختلاف فالعنوان."
    elif has_unverified_discrepancy:
        reason_fr = "Les pièces sont présentes, mais la concordance d'adresse n'a pas pu être vérifiée."
        reason_ar = "الوثائق موجودة ولكن ما قدرناش نتحققو من تطابق العنوان."
    else:
        reason_fr = "Toutes les pièces requises sont présentes et les contrôles disponibles sont concordants."
        reason_ar = "كاع الوثائق المطلوبة موجودة والمعلومات اللي قدرنا نتحققو منها متطابقة."

    code = tracking_code(case.public_id, case.created_at)
    requested_label = (missing or unreadable)
    missing_name = requested_label[0]["labelFr"] if requested_label else ("Correction de l'adresse" if has_mismatch else "Justificatif lisible avec adresse")
    messages = notification_draft(case.status, code, missing_document=missing_name) if recommendation == "REQUEST_CHANGES" else notification_draft("DOCS_APPROVED", code)
    summary_fr = f"Documents : {present}/{len(required)} conformes. {discrepancies[0]['detailFr']} Recommandation : {'approuver' if recommendation == 'APPROVE' else 'demander des modifications'}."
    summary_ar = f"الوثائق: {present}/{len(required)} مطابقة. {discrepancies[0]['detailAr']} التوصية: {'الموافقة' if recommendation == 'APPROVE' else 'طلب التصحيح'}."
    return {
        "caseId": case.public_id,
        "trackingCode": code,
        "serviceId": case.service_id,
        "executiveSummary": {"fr": summary_fr, "darija": summary_ar},
        "documentsCheck": {"present": present, "required": len(required), "items": checks},
        "discrepancyChecks": discrepancies,
        "recommendation": {
            "action": recommendation,
            "reasonFr": reason_fr,
            "reasonDarija": reason_ar,
        },
        "notificationDraft": messages,
        "generatedAt": datetime.now(UTC).isoformat(),
        "decisionSupportOnly": True,
    }
