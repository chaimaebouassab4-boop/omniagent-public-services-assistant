export const CASE_STEPS = ["DRAFT", "SUBMITTED", "UNDER_REVIEW", "DOCS_APPROVED", "READY_FOR_PICKUP"] as const;
export type CaseStatus = typeof CASE_STEPS[number] | "CHANGES_REQUESTED" | "RESUBMITTED" | "REJECTED";

const LEGACY: Record<string, CaseStatus> = {
  draft: "DRAFT",
  submitted: "SUBMITTED",
  in_review: "UNDER_REVIEW",
  pending_documents: "UNDER_REVIEW",
  approved: "READY_FOR_PICKUP",
};

export function canonicalCaseStatus(status: string): CaseStatus | null {
  const value = LEGACY[status] ?? status;
  return [...CASE_STEPS, "CHANGES_REQUESTED", "RESUBMITTED", "REJECTED"].includes(value) ? value as CaseStatus : null;
}

export const CASE_LABELS: Record<CaseStatus, { fr: string; ar: string }> = {
  CHANGES_REQUESTED: { fr: "Modifications demandées", ar: "تعديلات مطلوبة" },
  RESUBMITTED: { fr: "Resoumis", ar: "أعيد الإرسال" },
  REJECTED: { fr: "Rejeté", ar: "مرفوض" },
  DRAFT: { fr: "Brouillon", ar: "مسودة" },
  SUBMITTED: { fr: "Déposée", ar: "تم الإرسال" },
  UNDER_REVIEW: { fr: "En cours d'examen", ar: "قيد المراجعة" },
  DOCS_APPROVED: { fr: "Pièces validées", ar: "الوثائق مقبولة" },
  READY_FOR_PICKUP: { fr: "Prête au retrait", ar: "جاهزة للسحب" },
};

export const NEXT_ACTIONS: Record<CaseStatus, { fr: string; ar: string }> = {
  CHANGES_REQUESTED: { fr: "Corrigez les pièces et soumettez à nouveau.", ar: "صحح الوثائق وأعد إرسال الطلب." },
  RESUBMITTED: { fr: "Votre correction attend la revue.", ar: "التعديلات في انتظار المراجعة." },
  REJECTED: { fr: "Consultez la décision dans l’historique.", ar: "راجع القرار في السجل." },
  DRAFT: { fr: "Vérifiez et soumettez votre demande.", ar: "راجع طلبك ثم أرسله." },
  SUBMITTED: { fr: "Aucune action requise pour le moment.", ar: "لا يلزمك أي إجراء حالياً." },
  UNDER_REVIEW: { fr: "Consultez les demandes de documents complémentaires.", ar: "تحقق من طلبات الوثائق الإضافية." },
  DOCS_APPROVED: { fr: "Attendez votre convocation.", ar: "انتظر الاستدعاء." },
  READY_FOR_PICKUP: { fr: "Présentez le reçu et votre CIN au guichet.", ar: "قدم الوصل وبطاقة التعريف للشباك." },
};

export function nextCaseStatus(status: string): CaseStatus | null {
  if (status === "rejected") return "UNDER_REVIEW";
  const canonical = canonicalCaseStatus(status);
  if (!canonical) return null;
  if (canonical === "RESUBMITTED") return "UNDER_REVIEW";
  if (canonical === "CHANGES_REQUESTED" || canonical === "REJECTED") return null;
  return CASE_STEPS[CASE_STEPS.indexOf(canonical) + 1] ?? null;
}
