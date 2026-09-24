import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  getAdminCaseAiSummaryQueryKey,
  getAdminListCasesQueryKey,
  getGetAdminStatsQueryKey,
  useAdminCaseAction,
  useAdminCaseAiSummary,
  type AdminActionResult,
} from "@workspace/api-client-react";
import { useI18n } from "@/lib/i18n";
import { useToast } from "@/hooks/use-toast";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import {
  AlertTriangle,
  BrainCircuit,
  Check,
  CheckCircle2,
  Loader2,
  MessageSquareWarning,
  RefreshCw,
  ShieldCheck,
  XCircle,
} from "lucide-react";

type AdminCopilotCardProps = {
  caseId: number;
  onCompleted?: (result: AdminActionResult) => void;
};

export function AdminCopilotCard({ caseId, onCompleted }: AdminCopilotCardProps) {
  const { language, isRtl } = useI18n();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const summaryQuery = useAdminCaseAiSummary(caseId);
  const actionMutation = useAdminCaseAction();
  const [requestOpen, setRequestOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [messageFr, setMessageFr] = useState("");
  const [messageDarija, setMessageDarija] = useState("");
  const [preview, setPreview] = useState<AdminActionResult["notificationPreview"] | null>(null);

  const summary = summaryQuery.data;
  const localized = (fr: string, darija: string) => language === "fr" ? fr : darija;

  const refresh = async (result: AdminActionResult) => {
    setPreview(result.notificationPreview);
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: getAdminListCasesQueryKey() }),
      queryClient.invalidateQueries({ queryKey: getGetAdminStatsQueryKey() }),
      queryClient.invalidateQueries({ queryKey: ["admin", "notifications"] }),
      queryClient.invalidateQueries({ queryKey: ["case", caseId] }),
      queryClient.invalidateQueries({ queryKey: ["case-timeline", caseId] }),
      queryClient.invalidateQueries({ queryKey: ["cases"] }),
      queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      queryClient.invalidateQueries({ queryKey: getAdminCaseAiSummaryQueryKey(caseId) }),
    ]);
    onCompleted?.(result);
  };

  const handleError = (error: Error) => {
    toast({
      variant: "destructive",
      title: localized("Action impossible", "تعذر تنفيذ الإجراء"),
      description: error.message,
    });
  };

  const approve = () => {
    actionMutation.mutate(
      { id: caseId, action: "approve" },
      { onSuccess: refresh, onError: handleError },
    );
  };

  const openRequest = () => {
    if (!summary) return;
    setReason(summary.recommendation.reasonFr);
    setMessageFr(summary.notificationDraft.fr);
    setMessageDarija(summary.notificationDraft.darija);
    setRequestOpen(true);
  };

  const requestChanges = () => {
    actionMutation.mutate(
      {
        id: caseId,
        action: "request-changes",
        data: { reason, messageFr, messageDarija },
      },
      {
        onSuccess: async (result) => {
          setRequestOpen(false);
          await refresh(result);
        },
        onError: handleError,
      },
    );
  };

  if (summaryQuery.isLoading) {
    return (
      <Card className="border-primary/20">
        <CardContent className="flex items-center gap-3 py-8 text-sm text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin text-primary" />
          {localized("Analyse du dossier en cours…", "جاري تحليل الملف…")}
        </CardContent>
      </Card>
    );
  }

  if (summaryQuery.isError || !summary) {
    return (
      <Card className="border-red-200">
        <CardContent className="space-y-3 py-6">
          <p className="text-sm text-red-700 dark:text-red-300">
            {localized("La synthèse Copilot est indisponible.", "ملخص Copilot غير متاح.")}
          </p>
          <Button size="sm" variant="outline" onClick={() => summaryQuery.refetch()} className="gap-2">
            <RefreshCw className="h-4 w-4" />
            {localized("Réessayer", "إعادة المحاولة")}
          </Button>
        </CardContent>
      </Card>
    );
  }

  const canApprove = summary.recommendation.action === "APPROVE";
  const progress = summary.documentsCheck.required
    ? Math.round((summary.documentsCheck.present / summary.documentsCheck.required) * 100)
    : 0;

  return (
    <>
      <Card className="overflow-hidden border-primary/30 shadow-sm" dir={isRtl ? "rtl" : "ltr"}>
        <CardHeader className="border-b bg-gradient-to-r from-primary/10 via-primary/5 to-transparent pb-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <BrainCircuit className="h-5 w-5 text-primary" />
              {localized("Copilot agent public", "مساعد الموظف العمومي")}
            </CardTitle>
            <Badge variant="outline" className="gap-1 border-primary/30 bg-background">
              <ShieldCheck className="h-3.5 w-3.5" />
              {localized("Aide à la décision", "مساعدة فالقرار")}
            </Badge>
          </div>
          <p className="text-sm leading-6 text-muted-foreground">
            {localized(summary.executiveSummary.fr, summary.executiveSummary.darija)}
          </p>
        </CardHeader>
        <CardContent className="space-y-5 p-5">
          <section className="space-y-3">
            <div className="flex items-center justify-between gap-3 text-sm">
              <span className="font-semibold">{localized("Contrôle des pièces", "مراقبة الوثائق")}</span>
              <span className="font-mono text-primary">
                {summary.documentsCheck.present}/{summary.documentsCheck.required}
              </span>
            </div>
            <Progress value={progress} className="h-2" />
            <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
              {summary.documentsCheck.items.map((item) => {
                const ok = item.status === "PRESENT";
                const Icon = ok ? CheckCircle2 : item.status === "UNREADABLE" ? AlertTriangle : XCircle;
                return (
                  <div key={item.requirement} className="flex items-start gap-2 rounded-lg border bg-muted/20 p-2.5">
                    <Icon className={`mt-0.5 h-4 w-4 shrink-0 ${ok ? "text-emerald-600" : "text-red-600"}`} />
                    <div className="min-w-0">
                      <p className="truncate text-xs font-medium">{localized(item.labelFr, item.labelAr)}</p>
                      <p className={`text-[11px] ${ok ? "text-emerald-700" : "text-red-700"}`}>
                        {item.status === "PRESENT"
                          ? localized("Présent", "موجود")
                          : item.status === "UNREADABLE"
                            ? localized("Illisible", "ما مقروءاش")
                            : localized("Manquant", "ناقص")}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          <section className="space-y-2">
            {summary.discrepancyChecks.map((check) => (
              <div key={check.field} className="flex items-start justify-between gap-3 rounded-lg border p-3 text-sm">
                <span className="text-muted-foreground">{localized(check.detailFr, check.detailAr)}</span>
                <Badge className={check.status === "MATCH" || check.status === "NOT_APPLICABLE" ? "bg-emerald-600" : "bg-amber-600"}>
                  {check.status.replaceAll("_", " ")}
                </Badge>
              </div>
            ))}
          </section>

          <Alert className={canApprove ? "border-emerald-300 bg-emerald-50/70 dark:bg-emerald-950/20" : "border-amber-300 bg-amber-50/70 dark:bg-amber-950/20"}>
            {canApprove ? <CheckCircle2 className="h-4 w-4 text-emerald-700" /> : <AlertTriangle className="h-4 w-4 text-amber-700" />}
            <AlertTitle>{canApprove ? localized("Recommandation : approuver", "التوصية: الموافقة") : localized("Recommandation : demander des modifications", "التوصية: طلب التصحيح")}</AlertTitle>
            <AlertDescription>
              {localized(summary.recommendation.reasonFr, summary.recommendation.reasonDarija)}
            </AlertDescription>
          </Alert>

          {preview && (
            <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 text-sm">
              <div className="mb-2 flex items-center gap-2 font-semibold">
                <MessageSquareWarning className="h-4 w-4 text-primary" />
                {localized(`Aperçu ${preview.channel} — non envoyé`, `معاينة ${preview.channel} — ما تصيفطاتش`)}
              </div>
              <p className="text-muted-foreground">FR · {preview.fr}</p>
              <p className="mt-2 text-muted-foreground" dir="rtl">الدارجة · {preview.darija}</p>
            </div>
          )}

          <div className="flex flex-wrap gap-2">
            <Button onClick={approve} disabled={!canApprove || actionMutation.isPending} className="gap-2 bg-emerald-600 hover:bg-emerald-700">
              {actionMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
              {localized("Approuver", "الموافقة")}
            </Button>
            <Button onClick={openRequest} disabled={actionMutation.isPending} variant="outline" className="gap-2">
              <MessageSquareWarning className="h-4 w-4" />
              {localized("Demander des modifications", "طلب التصحيح")}
            </Button>
          </div>
          <p className="text-[11px] text-muted-foreground">
            {localized("Le Copilot ne prend aucune décision officielle. L'agent reste responsable de la validation.", "Copilot ما كياخد حتى قرار رسمي. الموظف هو المسؤول على المصادقة.")}
          </p>
        </CardContent>
      </Card>

      <Dialog open={requestOpen} onOpenChange={setRequestOpen}>
        <DialogContent dir={isRtl ? "rtl" : "ltr"}>
          <DialogHeader>
            <DialogTitle>{localized("Demander des modifications", "طلب التصحيح")}</DialogTitle>
            <DialogDescription>
              {localized("Vérifiez les messages préremplis avant de créer l'aperçu SMS / WhatsApp.", "راجع الرسائل المعمرة قبل إنشاء معاينة SMS / WhatsApp.")}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <label className="block space-y-1.5 text-sm font-medium">
              <span>{localized("Motif interne", "السبب الداخلي")}</span>
              <Textarea value={reason} onChange={(event) => setReason(event.target.value)} maxLength={320} />
            </label>
            <label className="block space-y-1.5 text-sm font-medium">
              <span>Message français</span>
              <Textarea value={messageFr} onChange={(event) => setMessageFr(event.target.value)} maxLength={500} />
            </label>
            <label className="block space-y-1.5 text-sm font-medium">
              <span>رسالة بالدارجة</span>
              <Textarea dir="rtl" value={messageDarija} onChange={(event) => setMessageDarija(event.target.value)} maxLength={500} />
            </label>
          </div>
          <DialogFooter>
            <Button
              onClick={requestChanges}
              disabled={!reason.trim() || !messageFr.trim() || !messageDarija.trim() || actionMutation.isPending}
              className="gap-2"
            >
              {actionMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              {localized("Créer l'aperçu", "إنشاء المعاينة")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
