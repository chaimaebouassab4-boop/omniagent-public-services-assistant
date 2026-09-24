"""Canonical case states and transition rules shared by both API contracts."""

from datetime import datetime

CASE_STEPS = (
    "DRAFT",
    "SUBMITTED",
    "UNDER_REVIEW",
    "DOCS_APPROVED",
    "READY_FOR_PICKUP",
)

LEGACY_STATUSES = {
    "draft": "DRAFT",
    "submitted": "SUBMITTED",
    "in_review": "UNDER_REVIEW",
    "pending_documents": "UNDER_REVIEW",
    "approved": "READY_FOR_PICKUP",
}

NEXT_ACTIONS = {
    "DRAFT": {"fr": "Vérifiez votre demande et soumettez-la.", "ar": "راجع طلبك ثم أرسله."},
    "SUBMITTED": {"fr": "Aucune action requise. Votre dossier attend sa prise en charge.", "ar": "لا يلزمك أي إجراء. طلبك في انتظار المعالجة."},
    "UNDER_REVIEW": {"fr": "Suivez les demandes de documents complémentaires.", "ar": "تابع طلبات الوثائق الإضافية."},
    "DOCS_APPROVED": {"fr": "Aucune action requise. La convocation est en préparation.", "ar": "لا يلزمك أي إجراء. الاستدعاء قيد الإعداد."},
    "READY_FOR_PICKUP": {"fr": "Présentez ce reçu et votre CIN au guichet pour retirer votre document.", "ar": "قدم هذا الوصل وبطاقة التعريف الوطنية لسحب الوثيقة."},
}


def canonical_status(value: str) -> str:
    return LEGACY_STATUSES.get(value, value)


def next_status(value: str) -> str | None:
    status = canonical_status(value)
    if status not in CASE_STEPS:
        return None
    index = CASE_STEPS.index(status)
    return CASE_STEPS[index + 1] if index + 1 < len(CASE_STEPS) else None


def validate_transition(current: str, target: str, *, is_admin: bool) -> str:
    """Return a canonical target or reject skipped, backward, and unauthorized steps."""
    target = canonical_status(target)
    if current == "rejected" and target == "UNDER_REVIEW" and is_admin:
        return target  # A legacy rejected case can be reopened into the new workflow.
    expected = next_status(current)
    if target not in CASE_STEPS or target != expected:
        raise ValueError(f"Invalid case transition: {canonical_status(current)} -> {target}. Expected: {expected or 'none'}.")
    if canonical_status(current) != "DRAFT" and not is_admin:
        raise PermissionError("Only an administrator can advance a submitted case.")
    return target


def tracking_code(public_id: int, created_at: datetime) -> str:
    return f"MA-{created_at.year}-{public_id:06d}"
