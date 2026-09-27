import type { Case } from "@/lib/api-client";
import { useI18n } from "@/lib/i18n";
import { CASE_LABELS, CASE_STEPS, NEXT_ACTIONS, canonicalCaseStatus } from "@/lib/case-lifecycle";
import { Check, Circle } from "lucide-react";

export function CaseProgressTimeline({ caseData, compact = false }: { caseData: Case; compact?: boolean }) {
  const { language, isRtl } = useI18n();
  const current = canonicalCaseStatus(caseData.status);
  const activeIndex = CASE_STEPS.findIndex(step => step === current);
  const locale = language === "fr" ? "fr-MA" : "ar-MA";
  const action = current
    ? (language === "fr" ? caseData.nextAction ?? NEXT_ACTIONS[current].fr : caseData.nextActionAr ?? NEXT_ACTIONS[current].ar)
    : (language === "fr" ? "Contactez l'administration pour ce dossier." : "تواصل مع الإدارة بخصوص هذا الملف.");

  return (
    <div className={compact ? "space-y-3" : "space-y-5"} dir={isRtl ? "rtl" : "ltr"}>
      {current && activeIndex < 0 && <p className="rounded-lg border p-3 font-semibold">{CASE_LABELS[current][language === "fr" ? "fr" : "ar"]}</p>}
      <ol className={compact ? "grid gap-2 sm:grid-cols-5" : "space-y-2"} aria-label={language === "fr" ? "Étapes du dossier" : "مراحل الطلب"}>
        {CASE_STEPS.map((step, index) => {
          const reached = index <= activeIndex;
          const active = index === activeIndex;
          const entry = caseData.statusHistory?.find((item) => canonicalCaseStatus(item.status) === step);
          return (
            <li key={step} aria-current={active ? "step" : undefined}
              className={`rounded-xl border p-3 ${active ? "border-primary bg-primary/10 ring-1 ring-primary/30" : reached ? "border-emerald-300 bg-emerald-50/60 dark:border-emerald-800 dark:bg-emerald-950/20" : "border-border bg-muted/20"}`}>
              <div className="flex items-center gap-2">
                <span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold ${active ? "bg-primary text-primary-foreground" : reached ? "bg-emerald-600 text-white" : "bg-muted text-muted-foreground"}`}>
                  {reached && !active ? <Check className="h-4 w-4" /> : active ? index + 1 : <Circle className="h-3 w-3" />}
                </span>
                <span className="text-xs font-semibold leading-tight">{language === "fr" ? CASE_LABELS[step].fr : CASE_LABELS[step].ar}</span>
              </div>
              {entry && reached && <time dateTime={entry.occurredAt} className="mt-2 block text-[11px] text-muted-foreground">
                {new Date(entry.occurredAt).toLocaleString(locale, { dateStyle: "short", timeStyle: "short" })}
              </time>}
              {active && <span className="mt-1 block text-[11px] font-medium text-primary">{language === "fr" ? "Étape actuelle" : "المرحلة الحالية"}</span>}
            </li>
          );
        })}
      </ol>
      {!compact && <div className="rounded-xl border border-primary/20 bg-primary/5 p-3 text-sm">
        <span className="font-semibold">{language === "fr" ? "Prochaine action : " : "الخطوة التالية: "}</span>
        {action}
      </div>}
    </div>
  );
}
