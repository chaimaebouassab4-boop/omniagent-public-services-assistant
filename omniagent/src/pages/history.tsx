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
      <div className="max-w-3xl mx-auto space-y-8">
        {/* Header */}
        <div className={`flex items-center justify-between ${isRtl ? "flex-row-reverse" : ""}`}>
          <div className={isRtl ? "text-right" : ""}>
            <h1 className="text-3xl font-bold text-foreground flex items-center gap-3">
              <History className="w-7 h-7 text-primary" />
              {language === "fr" ? "Historique et suivi" : "سجل وتتبع الطلبات"}
            </h1>
            <p className="text-muted-foreground mt-1 text-sm">
              {language === "fr"
                ? "Consultez l’évolution de vos dossiers et les prochaines étapes."
                : "اطلع على تقدم ملفاتك والخطوات المقبلة."}
            </p>
          </div>
        </div>

        <section className="space-y-4" aria-label={language === "fr" ? "Suivi des dossiers" : "تتبع الطلبات"}>
          <h2 className="text-xl font-semibold">{language === "fr" ? "Mes dossiers" : "طلباتي"}</h2>
          {casesLoading && <p className="text-sm text-muted-foreground">{language === "fr" ? "Chargement des dossiers…" : "جاري تحميل الطلبات…"}</p>}
          {!casesLoading && !cases.length && <div className="rounded-xl border border-dashed p-6 text-sm text-muted-foreground">
            {language === "fr" ? "Aucun dossier pour le moment." : "ما كاين حتى طلب دابا."}
          </div>}
          {cases.map((caseItem) => <div key={caseItem.id} className="rounded-xl border bg-card p-4 space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="font-semibold">{language === "fr" ? caseItem.service?.nameFr : caseItem.service?.nameAr}</p>
                <p className="text-xs text-muted-foreground font-mono">{caseItem.trackingCode ?? caseItem.referenceNumber}</p>
              </div>
              <StatusBadge status={caseItem.status} />
            </div>
            <CaseProgressTimeline caseData={caseItem} compact />
            <div className="flex items-center justify-between gap-3 text-xs text-muted-foreground">
              <span>{language === "fr" ? caseItem.nextAction : caseItem.nextActionAr}</span>
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
