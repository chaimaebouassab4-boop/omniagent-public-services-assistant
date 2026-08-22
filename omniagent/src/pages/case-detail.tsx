import { useI18n } from "@/lib/i18n";
import { AppLayout } from "@/components/layout/AppLayout";
import {
  useGetCase,
  useGetCaseTimeline,
  useListMessages,
  useSendMessage,
  useListDocuments,
  getListMessagesQueryKey,
  getListDocumentsQueryKey,
} from "@workspace/api-client-react";
import { useParams } from "wouter";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "./dashboard";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Upload, Mic, Send, Bot, User, CheckCircle2, Clock, FileText, Loader2, Eye, Download, Trash2, AlertTriangle } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";
import { uploadDocument, validateFile, fetchCaseDocPreview, deleteCaseDocument } from "@/lib/documents";
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
  const { data: caseData, isLoading: caseLoading } = useGetCase(caseId, { query: { enabled: !!caseId, queryKey: ['case', caseId] as any } });
  const { data: timeline } = useGetCaseTimeline(caseId, { query: { enabled: !!caseId, queryKey: ['case-timeline', caseId] as any } });
  const { data: messages } = useListMessages(caseId, { query: { enabled: !!caseId, queryKey: getListMessagesQueryKey(caseId) as any } });
  const { data: documents } = useListDocuments(caseId, { query: { enabled: !!caseId, queryKey: getListDocumentsQueryKey(caseId) as any } });
  const sendMessage = useSendMessage();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [messageInput, setMessageInput] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [previewDoc, setPreviewDoc] = useState<{ name: string; url: string; mimeType: string } | null>(null);
  const [previewLoadingId, setPreviewLoadingId] = useState<number | string | null>(null);
  const [docToDelete, setDocToDelete] = useState<any | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
      await uploadDocument(caseId, file);
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

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, sendMessage.isPending]);

  const handleSendMessage = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!messageInput.trim() || !caseId) return;

    sendMessage.mutate(
      { id: caseId, data: { content: messageInput, language: language as "ar"|"fr"|"darija" } },
      {
        onSuccess: () => {
          setMessageInput("");
          queryClient.invalidateQueries({ queryKey: getListMessagesQueryKey(caseId) });
        }
      }
    );
  };

  const prompts = language === "fr" 
    ? ["Comment renouveler ma carte ?", "Quels sont les documents manquants ?"] 
    : ["كيفاش نجدد بطاقة التعريف؟", "شنو هي الوثائق اللي خصني نجيب؟"];

  return (
    <AppLayout>
      <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Case Info & Chat */}
        <div className="lg:col-span-2 space-y-6 flex flex-col h-[calc(100vh-120px)]">
          {/* Header */}
          <Card className="shrink-0">
            <CardContent className="p-6">
              {caseLoading ? (
                <div className="space-y-2"><Skeleton className="h-6 w-1/3" /><Skeleton className="h-4 w-1/4" /></div>
              ) : (
                <div className="flex justify-between items-start">
                  <div>
                    <h1 className="text-2xl font-bold mb-1">
                      {language === "fr" ? caseData?.service?.nameFr : caseData?.service?.nameAr}
                    </h1>
                    <div className="text-sm text-muted-foreground">Ref: {caseData?.referenceNumber}</div>
                  </div>
                  <StatusBadge status={caseData?.status || ""} />
                </div>
              )}
            </CardContent>
          </Card>

          {/* AI Chat Panel */}
          <Card className="flex-1 flex flex-col min-h-0 overflow-hidden border-primary/20 shadow-md">
            <CardHeader className="py-3 px-4 border-b bg-muted/30 shrink-0">
              <CardTitle className="text-sm flex items-center gap-2">
                <Bot className="w-5 h-5 text-primary" />
                {t("nav.chat")}
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
              <ScrollArea className="flex-1 p-4" viewportRef={scrollRef}>
                <div className="space-y-4">
                  {messages?.map((msg) => (
                    <div key={msg.id} className={`flex gap-3 max-w-[80%] ${msg.role === 'user' ? (isRtl ? 'mr-auto flex-row-reverse' : 'ml-auto flex-row-reverse') : (isRtl ? 'ml-auto' : 'mr-auto')}`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-secondary text-white' : 'bg-primary text-white'}`}>
                        {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                      </div>
                      <div className={`p-3 rounded-2xl text-sm ${msg.role === 'user' ? 'bg-secondary text-white rounded-tr-none' : 'bg-muted rounded-tl-none'}`}>
                        {msg.content}
                      </div>
                    </div>
                  ))}
                  {sendMessage.isPending && (
                    <div className={`flex gap-3 max-w-[80%] ${isRtl ? 'ml-auto' : 'mr-auto'}`}>
                      <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 bg-primary text-white">
                        <Bot className="w-4 h-4" />
                      </div>
                      <div className="p-3 rounded-2xl text-sm bg-muted rounded-tl-none flex items-center gap-1">
                        <span className="w-2 h-2 bg-primary/50 rounded-full animate-bounce"></span>
                        <span className="w-2 h-2 bg-primary/50 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></span>
                        <span className="w-2 h-2 bg-primary/50 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></span>
                      </div>
                    </div>
                  )}
                </div>
              </ScrollArea>
              
              {/* Chat Input */}
              <div className="p-4 border-t bg-background shrink-0">
                <div className="flex gap-2 mb-3 overflow-x-auto pb-2 scrollbar-hide">
                  {prompts.map((p, i) => (
                    <button 
                      key={i} 
                      onClick={() => setMessageInput(p)}
                      className="whitespace-nowrap px-3 py-1.5 bg-muted hover:bg-muted/80 text-xs rounded-full border transition-colors"
                    >
                      {p}
                    </button>
                  ))}
                </div>
                <form onSubmit={handleSendMessage} className="flex gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    className="shrink-0 text-muted-foreground"
                    disabled={isUploading}
                    onClick={() => fileInputRef.current?.click()}
                    title={language === "fr" ? "Joindre un document" : "إرفاق وثيقة"}
                  >
                    {isUploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                  </Button>
                  <Button type="button" variant="outline" size="icon" className="shrink-0 text-muted-foreground">
                    <Mic className="w-4 h-4" />
                  </Button>
                  <Input 
                    value={messageInput} 
                    onChange={e => setMessageInput(e.target.value)} 
                    placeholder={t("chat.placeholder")}
                    className="flex-1"
                  />
                  <Button type="submit" size="icon" disabled={!messageInput.trim() || sendMessage.isPending} className="shrink-0">
                    <Send className={`w-4 h-4 ${isRtl ? 'rotate-180' : ''}`} />
                  </Button>
                </form>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Timeline & Checklist */}
        <div className="space-y-6">
          {/* Hidden file input shared by the upload buttons */}
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf,image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={handleFileSelected}
            data-testid="input-document-file"
          />

          <Card>
            <CardHeader>
              <CardTitle className="text-base">{language === "fr" ? "Documents Requis" : "الوثائق المطلوبة"}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {caseData?.service?.requiredDocuments?.map((doc, idx) => (
                  <div key={idx} className="flex items-start gap-3 p-3 rounded-lg border bg-card">
                    <CheckCircle2 className="w-5 h-5 text-muted-foreground shrink-0 mt-0.5" />
                    <div className="text-sm font-medium">{doc}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Uploaded documents */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <CardTitle className="text-base">
                {language === "fr" ? "Mes Documents" : "وثائقي"}
              </CardTitle>
              <Button
                size="sm"
                variant="outline"
                className="gap-1.5"
                disabled={isUploading}
                onClick={() => fileInputRef.current?.click()}
                data-testid="button-upload-document"
              >
                {isUploading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
                {language === "fr" ? "Ajouter" : "إضافة"}
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {documents?.map((doc) => (
                  <div key={doc.id} className="flex items-center justify-between gap-3 p-3 rounded-lg border bg-card hover:bg-muted/20 transition-colors">
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                      <FileText className="w-5 h-5 text-primary shrink-0" />
                      <div className="min-w-0 flex-1">
                        <div className="text-sm font-medium truncate" title={doc.name}>{doc.name}</div>
                        <div className="text-xs text-muted-foreground">{formatFileSize(doc.fileSize)}</div>
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
              <div className="relative border-l-2 border-muted ml-3 pl-4 space-y-6">
                {timeline?.map((ev, idx) => (
                  <div key={ev.id} className="relative">
                    <div className="absolute -left-[23px] top-1 w-3 h-3 rounded-full bg-primary ring-4 ring-background" />
                    <div className="text-sm font-semibold">{language === "fr" ? ev.descriptionFr : ev.descriptionAr}</div>
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
