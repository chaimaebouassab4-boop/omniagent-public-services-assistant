import { useI18n } from "@/lib/i18n";
import { AppLayout } from "@/components/layout/AppLayout";
import { History } from "lucide-react";
import { Link } from "wouter";
import { useListCases } from "@workspace/api-client-react";
import { CaseProgressTimeline } from "@/components/cases/CaseProgressTimeline";
import { StatusBadge } from "./dashboard";

export default function HistoryPage() {
  const { language, isRtl } = useI18n();
  const { data: cases = [], isLoading: casesLoading } = useListCases();

  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto space-y-6 sm:space-y-8">
        {/* Header */}
        <div className={`flex items-center justify-between ${isRtl ? "flex-row-reverse" : ""}`}>
          <div className={isRtl ? "text-right" : ""}>
            <h1 className="text-2xl sm:text-3xl font-bold text-foreground flex items-center gap-2.5 sm:gap-3">
              <History className="w-6 h-6 sm:w-7 sm:h-7 text-primary shrink-0" />
              <span>{language === "fr" ? "Historique et suivi" : "سجل وتتبع الطلبات"}</span>
            </h1>
            <p className="text-muted-foreground mt-1 text-xs sm:text-sm">
              {language === "fr"
                ? "Consultez l’évolution de vos dossiers et les prochaines étapes."
                : "اطلع على تقدم ملفاتك والخطوات المقبلة."}
            </p>
          </div>
        </div>

        <section className="space-y-3 sm:space-y-4" aria-label={language === "fr" ? "Suivi des dossiers" : "تتبع الطلبات"}>
          <h2 className="text-lg sm:text-xl font-semibold">{language === "fr" ? "Mes dossiers" : "طلباتي"}</h2>
          {casesLoading && <p className="text-sm text-muted-foreground">{language === "fr" ? "Chargement des dossiers…" : "جاري تحميل الطلبات…"}</p>}
          {!casesLoading && !cases.length && <div className="rounded-xl border border-dashed p-4 sm:p-6 text-sm text-muted-foreground">
            {language === "fr" ? "Aucun dossier pour le moment." : "ما كاين حتى طلب دابا."}
          </div>}
          {cases.map((caseItem) => <div key={caseItem.id} className="rounded-xl border bg-card p-3.5 sm:p-4 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 sm:gap-2">
              <div>
                <p className="font-semibold text-sm sm:text-base leading-snug">{language === "fr" ? caseItem.service?.nameFr : caseItem.service?.nameAr}</p>
                <p className="text-xs text-muted-foreground font-mono mt-0.5">{caseItem.trackingCode ?? caseItem.referenceNumber}</p>
              </div>
              <div className="self-start sm:self-auto">
                <StatusBadge status={caseItem.status} />
              </div>
            </div>
            <CaseProgressTimeline caseData={caseItem} compact />
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-1.5 border-t border-border/50 sm:border-t-0 text-xs text-muted-foreground">
              <span className="leading-relaxed">{language === "fr" ? caseItem.nextAction : caseItem.nextActionAr}</span>
              <Link href={`/cases/${caseItem.id}`} className="shrink-0 font-medium text-primary hover:underline">
                {language === "fr" ? "Voir le dossier" : "عرض الطلب"}
              </Link>
            </div>
          </div>)}
        </section>

      </div>
    </AppLayout>
  );
}
