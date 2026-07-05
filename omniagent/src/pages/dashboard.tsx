import { useI18n } from "@/lib/i18n";
import { AppLayout } from "@/components/layout/AppLayout";
import { useGetDashboardSummary } from "@workspace/api-client-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Link } from "wouter";
import { FileText, Clock, CheckCircle, AlertCircle, ArrowRight, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export function StatusBadge({ status }: { status: string }) {
  const { t } = useI18n();
  
  let variant: "default" | "secondary" | "destructive" | "outline" = "default";
  let bgClass = "";
  
  switch(status) {
    case "approved": variant = "default"; bgClass = "bg-emerald-500/10 text-emerald-600 hover:bg-emerald-500/20 border-emerald-200 dark:border-emerald-800"; break;
    case "rejected": variant = "destructive"; bgClass = "bg-red-500/10 text-red-600 hover:bg-red-500/20 border-red-200 dark:border-red-800"; break;
    case "in_review": variant = "secondary"; bgClass = "bg-blue-500/10 text-blue-600 hover:bg-blue-500/20 border-blue-200 dark:border-blue-800"; break;
    case "pending_documents": variant = "outline"; bgClass = "bg-amber-500/10 text-amber-600 hover:bg-amber-500/20 border-amber-200 dark:border-amber-800"; break;
    default: variant = "outline"; bgClass = "bg-gray-500/10 text-gray-600 hover:bg-gray-500/20 border-gray-200 dark:border-gray-800"; break;
  }

  return (
    <Badge variant={variant} className={`${bgClass} border`}>
      {t(`status.${status}`)}
    </Badge>
  );
}

export default function Dashboard() {
  const { t, language, isRtl } = useI18n();
  const { data: summary, isLoading } = useGetDashboardSummary();
  const Arrow = isRtl ? ArrowLeft : ArrowRight;

  return (
    <AppLayout>
      <div className="max-w-6xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-foreground">{t("nav.dashboard")}</h1>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <Card key={i}><CardHeader><Skeleton className="h-4 w-1/2" /></CardHeader><CardContent><Skeleton className="h-8 w-1/4" /></CardContent></Card>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{t("dashboard.active")}</CardTitle>
                <FileText className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary?.activeCases || 0}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{t("dashboard.pending_docs")}</CardTitle>
                <AlertCircle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary?.pendingDocuments || 0}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{t("dashboard.avg_time")}</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary?.avgProcessingDays || 0} <span className="text-sm font-normal text-muted-foreground">{t("services.processing")}</span></div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{t("dashboard.approved")}</CardTitle>
                <CheckCircle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary?.approvedCases || 0}</div>
              </CardContent>
            </Card>
          </div>
        )}

        <div className="mt-12">
          <h2 className="text-xl font-bold mb-4">{language === "fr" ? "Dossiers Récents" : "القضايا الأخيرة"}</h2>
          
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
          ) : (
            <div className="bg-card border rounded-lg overflow-hidden">
              {summary?.recentCases?.length ? (
                <div className="divide-y divide-border">
                  {summary.recentCases.map((caseItem) => (
                    <div key={caseItem.id} className="p-4 flex items-center justify-between hover:bg-muted/50 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center shrink-0">
                          <FileText className="w-5 h-5 text-primary" />
                        </div>
                        <div>
                          <div className="font-semibold">{language === "fr" ? caseItem.service?.nameFr : caseItem.service?.nameAr}</div>
                          <div className="text-sm text-muted-foreground mt-1 flex items-center gap-2">
                            <span>Ref: {caseItem.referenceNumber}</span>
                            <span>•</span>
                            <span>{new Date(caseItem.submittedAt).toLocaleDateString(language === "fr" ? "fr-FR" : "ar-MA")}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <StatusBadge status={caseItem.status} />
                        <Button variant="ghost" size="icon" asChild>
                          <Link href={`/cases/${caseItem.id}`}>
                            <Arrow className="w-5 h-5 text-muted-foreground" />
                          </Link>
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-8 text-center text-muted-foreground">
                  {language === "fr" ? "Aucun dossier trouvé" : "لا توجد قضايا"}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
