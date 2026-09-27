import { useI18n } from "@/lib/i18n";
import { AppLayout } from "@/components/layout/AppLayout";
import {
  useGetCase,
  useGetCaseTimeline,
  useListDocuments,
  getListDocumentsQueryKey,
  useSubmitCase,
  downloadCaseReceipt,
} from "@workspace/api-client-react";
import { useParams } from "wouter";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "./dashboard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Upload, CheckCircle2, Clock, FileText, Loader2, Eye, Download, Trash2, AlertTriangle } from "lucide-react";
import { useState, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";
import { uploadDocument, validateFile, fetchCaseDocPreview, deleteCaseDocument } from "@/lib/documents";
import { CaseProgressTimeline } from "@/components/cases/CaseProgressTimeline";
import { canonicalCaseStatus } from "@/lib/case-lifecycle";
import { getStoredUser } from "@/lib/auth";
import { AdminCopilotCard } from "@/components/admin/AdminCopilotCard";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

function formatFileSize(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

export default function CaseDetail() {
  const { id } = useParams();
  const caseId = parseInt(id || "0", 10);
  const { t, language, isRtl } = useI18n();
  const isAdmin = !!getStoredUser()?.isAdmin;
  const { data: caseData, isLoading: caseLoading } = useGetCase(caseId, { query: { enabled: !!caseId, queryKey: ['case', caseId] as any } });
  const { data: timeline } = useGetCaseTimeline(caseId, { query: { enabled: !!caseId, queryKey: ['case-timeline', caseId] as any } });
  const { data: documents } = useListDocuments(caseId, { query: { enabled: !!caseId, queryKey: getListDocumentsQueryKey(caseId) as any } });
  const submitCase = useSubmitCase(caseData?.status === "CHANGES_REQUESTED" ? "RESUBMITTED" : "SUBMITTED");
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [uploadType, setUploadType] = useState("other");
  const [isUploading, setIsUploading] = useState(false);
  const [previewDoc, setPreviewDoc] = useState<{ name: string; url: string; mimeType: string } | null>(null);
  const [previewLoadingId, setPreviewLoadingId] = useState<number | string | null>(null);
  const [docToDelete, setDocToDelete] = useState<any | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isDownloadingReceipt, setIsDownloadingReceipt] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleReceipt = async () => {
    setIsDownloadingReceipt(true);
    try {
      await downloadCaseReceipt(caseId, caseData?.trackingCode);
    } catch (err) {
      toast({
        variant: "destructive",
        title: language === "fr" ? "Reçu indisponible" : "تعذر تحميل الوصل",
        description: err instanceof Error ? err.message : undefined,
      });
    } finally {
      setIsDownloadingReceipt(false);
    }
  };

  const handleSubmitDraft = () => {
    submitCase.mutate(caseId, {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["case", caseId] });
        queryClient.invalidateQueries({ queryKey: ["case-timeline", caseId] });
        queryClient.invalidateQueries({ queryKey: ["cases"] });
        queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      },
      onError: (err) => toast({ variant: "destructive", title: language === "fr" ? "Envoi impossible" : "تعذر إرسال الطلب", description: err.message }),
    });
  };

  const handleViewDoc = async (doc: any) => {
    setPreviewLoadingId(doc.id);
    try {
      const blob = await fetchCaseDocPreview(caseId, doc.id);
      if (previewDoc?.url) URL.revokeObjectURL(previewDoc.url);
      const url = URL.createObjectURL(blob);
      setPreviewDoc({ name: doc.name, url, mimeType: blob.type || doc.fileType || "application/pdf" });
    } catch (err) {
      toast({
        variant: "destructive",
        title: language === "fr" ? "Impossible d'afficher le document" : "تعذر عرض الوثيقة",
        description: err instanceof Error ? err.message : undefined,
      });
    } finally {
      setPreviewLoadingId(null);
    }
  };

  const handleDownloadDoc = async (doc: any) => {
    try {
      const blob = await fetchCaseDocPreview(caseId, doc.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = doc.name;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      toast({
        variant: "destructive",
        title: language === "fr" ? "Échec du téléchargement" : "فشل التحميل",
        description: err instanceof Error ? err.message : undefined,
      });
    }
  };

  const confirmDeleteDoc = async () => {
    if (!docToDelete) return;
    setIsDeleting(true);
    try {
      await deleteCaseDocument(caseId, docToDelete.id);
      toast({
        title: language === "fr" ? "Document supprimé" : "تم حذف الوثيقة بنجاح",
        description: docToDelete.name,
      });
      setDocToDelete(null);
      queryClient.invalidateQueries({ queryKey: getListDocumentsQueryKey(caseId) });
      queryClient.invalidateQueries({ queryKey: ['case-timeline', caseId] });
      queryClient.invalidateQueries({ queryKey: ['case', caseId] });
    } catch (err) {
      toast({
        variant: "destructive",
        title: language === "fr" ? "Échec de suppression" : "فشل الحذف",
        description: err instanceof Error ? err.message : undefined,
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const handleFileSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = ""; // allow re-selecting the same file
    if (!file || !caseId) return;

    const validationError = validateFile(file);
    if (validationError) {
      toast({
        variant: "destructive",
        title: language === "fr" ? "Fichier refusé" : "الملف مرفوض",
        description:
          validationError === "too_large"
            ? (language === "fr" ? "Taille maximale : 10 MB." : "الحجم الأقصى: 10 ميغابايت.")
            : (language === "fr" ? "Formats acceptés : PDF, JPEG, PNG, WebP." : "الصيغ المقبولة: PDF, JPEG, PNG, WebP."),
      });
      return;
    }

    setIsUploading(true);
    try {
      await uploadDocument(caseId, file, uploadType);
      queryClient.invalidateQueries({ queryKey: ['case', caseId] });
      toast({
        title: language === "fr" ? "Document envoyé" : "تم إرسال الوثيقة",
        description: file.name,
      });
      queryClient.invalidateQueries({ queryKey: getListDocumentsQueryKey(caseId) });
      queryClient.invalidateQueries({ queryKey: ['case-timeline', caseId] });
    } catch (err) {
      toast({
        variant: "destructive",
        title: language === "fr" ? "Échec de l'envoi" : "فشل الإرسال",
        description: err instanceof Error ? err.message : undefined,
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <AppLayout>
      <div className="max-w-6xl mx-auto space-y-6 min-w-0">
        
        {/* Case information */}
        <div className="space-y-6 min-w-0">
          {/* Header */}
          {isAdmin && caseData && <Card><CardHeader><CardTitle>{language === "fr" ? "Informations du citoyen à la soumission" : "معلومات المواطن عند الإرسال"}</CardTitle></CardHeader><CardContent className="space-y-2 text-sm">
            <p>{caseData.profileSnapshot?.fullName ?? caseData.applicantName}</p>
            <p>{caseData.profileSnapshot?.email ?? caseData.applicantEmail}</p>
            <p>{caseData.profileSnapshot?.phone ?? caseData.applicantPhone}</p>
            <p>{caseData.profileSnapshot?.address}</p>
            <p className="whitespace-pre-wrap">{caseData.notes}</p>
          </CardContent></Card>}
          <Card className="shrink-0">
            <CardContent className="p-6">
              {caseLoading ? (
                <div className="space-y-2"><Skeleton className="h-6 w-1/3" /><Skeleton className="h-4 w-1/4" /></div>
              ) : (
                <div className="flex flex-wrap justify-between items-start gap-3">
                  <div>
                    <h1 className="text-2xl font-bold mb-1">
                      {language === "fr" ? caseData?.service?.nameFr : caseData?.service?.nameAr}
                    </h1>
                    <div className="text-sm text-muted-foreground">{language === "fr" ? "Suivi" : "رمز التتبع"}: {caseData?.trackingCode ?? caseData?.referenceNumber}</div>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge status={caseData?.status || ""} />
                    {caseData && ["DRAFT", "CHANGES_REQUESTED"].includes(caseData.status) ? (
                      <Button size="sm" onClick={handleSubmitDraft} disabled={submitCase.isPending}>
                        {submitCase.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : (language === "fr" ? "Soumettre" : "إرسال الطلب")}
                      </Button>
                    ) : caseData ? (
                      <Button size="sm" variant="outline" onClick={() => void handleReceipt()} disabled={isDownloadingReceipt} className="gap-2">
                        {isDownloadingReceipt ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
                        {language === "fr" ? "Reçu PDF" : "تحميل الوصل"}
                      </Button>
                    ) : null}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>


        </div>

        {/* Right Column: Timeline & Checklist */}
        <div className="grid items-start gap-6 lg:grid-cols-2 min-w-0">
          {isAdmin && caseId > 0 && <AdminCopilotCard caseId={caseId} />}
          {caseData && <Card>
            <CardHeader><CardTitle className="text-base">{language === "fr" ? "Suivi du dossier" : "تتبع الطلب"}</CardTitle></CardHeader>
            <CardContent><CaseProgressTimeline caseData={caseData} /></CardContent>
          </Card>}
          {/* Hidden file input shared by the upload buttons */}
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf,image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={handleFileSelected}
            data-testid="input-document-file"
          />

          <Card className="min-w-0">
            <CardHeader>
              <CardTitle className="text-base">{language === "fr" ? "Documents manquants ou à remplacer" : "الوثائق الناقصة أو المطلوب تعويضها"}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {caseLoading ? <Skeleton className="h-24" /> : !caseData?.documentChecklist ? (
                <p className="text-sm text-muted-foreground">{language === "fr" ? "Liste des pièces indisponible." : "قائمة الوثائق غير متاحة."}</p>
              ) : caseData.documentChecklist.filter(item => item.status !== "PRESENT").length === 0 ? (
                <p className="flex items-center gap-2 text-sm text-emerald-700"><CheckCircle2 className="h-5 w-5 shrink-0" />{language === "fr" ? "Toutes les pièces demandées sont déposées. Leur validation reste à la charge de l’administration." : "تم إيداع جميع الوثائق المطلوبة. المصادقة عليها تبقى من اختصاص الإدارة."}</p>
              ) : caseData.documentChecklist.filter(item => item.status !== "PRESENT").map(item => (
                <div key={item.requirement} className="flex flex-wrap items-center gap-3 rounded-xl border border-amber-200 bg-amber-50/40 p-3 dark:bg-amber-950/20">
                  <AlertTriangle className="h-5 w-5 shrink-0 text-amber-600" />
                  <div className="flex-1 min-w-0 text-sm">
                    <p className="font-medium break-words">{language === "fr" ? item.labelFr : item.labelAr}</p>
                    <p className="text-muted-foreground">{item.status === "UNREADABLE" ? (language === "fr" ? "À remplacer : pièce illisible ou rejetée" : "يجب تعويض الوثيقة غير المقروءة أو المرفوضة") : (language === "fr" ? "Non déposée" : "لم يتم إيداعها")}</p>
                  </div>
                  <Button size="sm" variant="outline" disabled={isUploading} onClick={() => { setUploadType(item.requirement); fileInputRef.current?.click(); }}>
                    <Upload className="h-4 w-4 me-2" />{language === "fr" ? "Déposer" : "إيداع"}
                  </Button>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Uploaded documents */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <CardTitle className="text-base">
                {language === "fr" ? "Documents déjà déposés" : "الوثائق المودعة"}
              </CardTitle>
              <Button
                size="sm"
                variant="outline"
                className="gap-1.5"
                disabled={isUploading}
                onClick={() => { setUploadType("other"); fileInputRef.current?.click(); }}
                data-testid="button-upload-document"
              >
                {isUploading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
                {language === "fr" ? "Ajouter" : "إضافة"}
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {documents?.map((doc) => (
                  <div key={doc.id} className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-lg border bg-card hover:bg-muted/20 transition-colors">
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                      <FileText className="w-5 h-5 text-primary shrink-0" />
                      <div className="min-w-0 flex-1">
                        <div className="text-sm font-medium truncate" title={doc.name}>{doc.name}</div>
                        <div className="text-xs text-muted-foreground">{formatFileSize(doc.fileSize)} · {new Date(doc.uploadedAt).toLocaleDateString(language === "fr" ? "fr-MA" : "ar-MA")}</div>
                        {isAdmin && <details className="mt-2 text-xs"><summary className="cursor-pointer">{language === "fr" ? "Extraction OCR / pré-contrôle" : "استخراج OCR / فحص أولي"}</summary>
                          <p>{doc.analysis?.extractionStatus ?? (language === "fr" ? "Non analysé" : "لم يتم التحليل")}</p>
                          {doc.analysis?.confidence_score != null && <p>{Math.round(doc.analysis.confidence_score * 100)}%</p>}
                          {doc.analysis?.warnings?.map((warning, index) => <p key={index}>{warning}</p>)}
                          <pre className="whitespace-pre-wrap break-words max-h-52 overflow-auto">{doc.analysis?.raw_extracted_text}</pre>
                        </details>}
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5 shrink-0">
                      <Badge
                        variant="outline"
                        className={
                          doc.status === "verified"
                            ? "border-green-300 bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300"
                            : doc.status === "rejected"
                            ? "border-red-300 bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300"
                            : "border-amber-300 bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300"
                        }
                      >
                        {doc.status === "verified"
                          ? (language === "fr" ? "Vérifié" : "تم التحقق")
                          : doc.status === "rejected"
                          ? (language === "fr" ? "Rejeté" : "مرفوض")
                          : (language === "fr" ? "En attente" : "قيد المراجعة")}
                      </Badge>

                      {/* View Button */}
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-8 w-8 text-primary hover:bg-primary/10"
                        title={language === "fr" ? "Voir la pièce" : "معاينة الوثيقة"}
                        disabled={previewLoadingId === doc.id}
                        onClick={() => handleViewDoc(doc)}
                      >
                        {previewLoadingId === doc.id ? (
                          <Loader2 className="w-4 h-4 animate-spin text-primary" />
                        ) : (
                          <Eye className="w-4 h-4" />
                        )}
                      </Button>

                      {/* Download Button */}
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-8 w-8 text-muted-foreground hover:text-foreground"
                        title={language === "fr" ? "Télécharger" : "تحميل"}
                        onClick={() => handleDownloadDoc(doc)}
                      >
                        <Download className="w-4 h-4" />
                      </Button>

                      {/* Delete Button */}
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/40"
                        title={language === "fr" ? "Supprimer" : "حذف الوثيقة"}
                        onClick={() => setDocToDelete(doc)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
                {!documents?.length && (
                  <div className="text-sm text-muted-foreground text-center py-4 border rounded-lg border-dashed">
                    {language === "fr" ? "Aucun document envoyé pour l'instant." : "لم يتم إرسال أي وثيقة بعد."}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">{language === "fr" ? "Historique" : "السجل"}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="relative border-s-2 border-muted ms-3 ps-4 space-y-6">
                {timeline?.map((ev, idx) => (
                  <div key={ev.id} className="relative">
                    <div className="absolute -start-[23px] top-1 w-3 h-3 rounded-full bg-primary ring-4 ring-background" />
                    <div className="text-sm font-semibold">{language === "fr" ? ev.descriptionFr : ev.descriptionAr}</div>
                    {(ev.decisionReason || ev.internalNote) && <p className="text-sm whitespace-pre-wrap">{ev.decisionReason || ev.internalNote}</p>}
                    <div className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(ev.occurredAt).toLocaleDateString()}
                    </div>
                  </div>
                ))}
                {!timeline?.length && (
                  <div className="text-sm text-muted-foreground">{language === "fr" ? "Aucun événement" : "لا يوجد سجل"}</div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

      </div>

      {/* Document Viewer Modal */}
      <Dialog
        open={Boolean(previewDoc)}
        onOpenChange={(open) => {
          if (!open && previewDoc) {
            URL.revokeObjectURL(previewDoc.url);
            setPreviewDoc(null);
          }
        }}
      >
        <DialogContent className="max-w-4xl h-[85vh] flex flex-col p-4 sm:p-6" dir={isRtl ? "rtl" : "ltr"}>
          <DialogHeader className="flex flex-row items-center justify-between pb-3 border-b">
            <div className="text-start">
              <DialogTitle className="text-base sm:text-lg font-bold truncate max-w-[500px]">
                {previewDoc?.name}
              </DialogTitle>
              <DialogDescription className="text-xs text-muted-foreground mt-0.5">
                {language === "fr" ? "Aperçu de la pièce justificative" : "معاينة الوثيقة المرفقة"}
              </DialogDescription>
            </div>
            {previewDoc && (
              <Button
                size="sm"
                variant="outline"
                className="gap-1.5 shrink-0"
                onClick={() => {
                  const a = document.createElement("a");
                  a.href = previewDoc.url;
                  a.download = previewDoc.name;
                  document.body.appendChild(a);
                  a.click();
                  document.body.removeChild(a);
                }}
              >
                <Download className="w-3.5 h-3.5" />
                <span>{language === "fr" ? "Télécharger" : "تحميل"}</span>
              </Button>
            )}
          </DialogHeader>
          <div className="flex-1 min-h-0 overflow-auto rounded-xl border bg-muted/30 flex items-center justify-center p-2">
            {previewDoc?.mimeType === "application/pdf" || previewDoc?.name.toLowerCase().endsWith(".pdf") ? (
              <iframe
                src={previewDoc.url}
                title={previewDoc.name}
                className="w-full h-full min-h-[60vh] rounded-lg"
              />
            ) : previewDoc ? (
              <img
                src={previewDoc.url}
                alt={previewDoc.name}
                className="max-w-full max-h-full object-contain rounded-lg shadow-sm"
              />
            ) : null}
          </div>
        </DialogContent>
      </Dialog>

      {/* Professional Delete Confirmation Modal */}
      <Dialog
        open={Boolean(docToDelete)}
        onOpenChange={(open) => {
          if (!open && !isDeleting) setDocToDelete(null);
        }}
      >
        <DialogContent className="max-w-md p-6 sm:p-7 rounded-2xl shadow-2xl" dir={isRtl ? "rtl" : "ltr"}>
          <div className="flex flex-col items-center text-center space-y-4 pt-2">
            <div className="w-14 h-14 rounded-full bg-red-100 dark:bg-red-950/60 flex items-center justify-center text-red-600 ring-8 ring-red-50 dark:ring-red-950/30">
              <Trash2 className="w-7 h-7" />
            </div>
            <div className="space-y-2">
              <DialogTitle className="text-xl font-bold">
                {language === "fr" ? "Supprimer le document ?" : "تأكيد حذف الوثيقة"}
              </DialogTitle>
              <DialogDescription className="text-sm text-muted-foreground leading-relaxed px-2">
                {language === "fr" ? (
                  <>
                    Êtes-vous sûr de vouloir supprimer définitivement <span className="font-semibold text-foreground font-mono text-xs px-1.5 py-0.5 rounded bg-muted">"{docToDelete?.name}"</span> ? Cette action ne peut pas être annulée.
                  </>
                ) : (
                  <>
                    هل أنت متأكد من رغبتك في حذف الوثيقة <span className="font-semibold text-foreground font-mono text-xs px-1.5 py-0.5 rounded bg-muted">"{docToDelete?.name}"</span> نهائياً؟ لن تتمكن من استرجاع هذا الملف.
                  </>
                )}
              </DialogDescription>
            </div>
          </div>
          <div className="flex items-center justify-center gap-3 pt-5 border-t mt-4">
            <Button
              variant="outline"
              className="flex-1 h-10 font-medium"
              disabled={isDeleting}
              onClick={() => setDocToDelete(null)}
            >
              {language === "fr" ? "Annuler" : "تراجع"}
            </Button>
            <Button
              variant="destructive"
              className="flex-1 h-10 gap-2 bg-red-600 hover:bg-red-700 text-white font-medium"
              disabled={isDeleting}
              onClick={confirmDeleteDoc}
            >
              {isDeleting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4" />
              )}
              <span>{language === "fr" ? "Supprimer" : "تأكيد الحذف"}</span>
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </AppLayout>
  );
}
