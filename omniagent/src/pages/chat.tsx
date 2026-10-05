import { useI18n } from "@/lib/i18n";
import { AppLayout } from "@/components/layout/AppLayout";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Upload, Mic, Send, User, FileText, Loader2, MessageSquarePlus,
  History, BookOpen, ShieldCheck, Trash2, Compass, FileCheck2, FolderClock,
  MoreHorizontal, MessageSquare,
  Landmark,
  Sparkles, ArrowUpRight, X, Image as ImageIcon, Volume2, Square,
} from "lucide-react";
import { useState, useRef, useEffect, useCallback } from "react";
import { useLocation } from "wouter";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";
import { uploadChatDocument, validateFile, analyzeAndExtractDocument, type ExtractedDocumentMetadata } from "@/lib/documents";
import { listChatSessions, listSessionMessages, sendSessionMessage, deleteChatSession, transcribeVoice, synthesizeVoice } from "@/lib/chat";
import type { ChatMessage } from "@/lib/chat";
import { ChatMessageContent } from "@/components/chat/ChatMessageContent";
import { useAudioRecorder } from "@/hooks/use-audio-recorder";
import { ExtractedDocumentCard, DocumentScanningSkeleton } from "@/components/chat/ExtractedDocumentCard";

const DOCUMENT_PREFIX = "[Document] ";

function formatFileSize(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

export default function Chat() {
  const { t, language, isRtl } = useI18n();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [_, setLocation] = useLocation();

  const [activeSessionId, setActiveSessionId] = useState("");
  const [messageInput, setMessageInput] = useState("");
  const [stagedFile, setStagedFile] = useState<File | null>(null);
  const [extractedDoc, setExtractedDoc] = useState<ExtractedDocumentMetadata | null>(null);
  const [isAnalyzingDoc, setIsAnalyzingDoc] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [playback, setPlayback] = useState<{ messageId: string; state: "loading" | "playing" } | null>(null);
  const [sessionToDelete, setSessionToDelete] = useState<string | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  /** Optimistic messages shown while waiting for RAG response */
  const [pendingUserMsg, setPendingUserMsg] = useState<ChatMessage | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const transcriptionAbortRef = useRef<AbortController | null>(null);
  const playbackRef = useRef<{ controller: AbortController; audio: HTMLAudioElement | null; url: string | null } | null>(null);
  const recorder = useAudioRecorder();

  const stopPlayback = useCallback(() => {
    const current = playbackRef.current;
    playbackRef.current = null;
    current?.controller.abort();
    if (current?.audio) {
      current.audio.onended = null;
      current.audio.onerror = null;
      current.audio.pause();
      current.audio.removeAttribute("src");
      current.audio.load();
    }
    if (current?.url) URL.revokeObjectURL(current.url);
    setPlayback(null);
  }, []);

  const playMessage = useCallback(async (message: ChatMessage) => {
    const messageId = String(message.id);
    if (playback?.messageId === messageId) {
      stopPlayback();
      return;
    }
    stopPlayback();
    const controller = new AbortController();
    const current = { controller, audio: null as HTMLAudioElement | null, url: null as string | null };
    playbackRef.current = current;
    setPlayback({ messageId, state: "loading" });
    try {
      const blob = await synthesizeVoice(message.content, language, controller.signal);
      if (controller.signal.aborted) return;
      current.url = URL.createObjectURL(blob);
      current.audio = new Audio(current.url);
      current.audio.onended = () => {
        if (playbackRef.current === current) stopPlayback();
      };
      current.audio.onerror = () => {
        if (playbackRef.current !== current) return;
        stopPlayback();
        toast({ variant: "destructive", title: language === "fr" ? "Lecture impossible" : "تعذر تشغيل الصوت" });
      };
      await current.audio.play();
      if (!controller.signal.aborted) setPlayback({ messageId, state: "playing" });
    } catch (error) {
      if (!controller.signal.aborted) {
        stopPlayback();
        toast({
          variant: "destructive",
          title: language === "fr" ? "Lecture impossible" : "تعذر تشغيل الصوت",
          description: error instanceof Error ? error.message : undefined,
        });
      }
    }
  }, [language, playback?.messageId, stopPlayback, toast]);

  useEffect(() => {
    recorder.cancel();
    transcriptionAbortRef.current?.abort();
    transcriptionAbortRef.current = null;
    setIsTranscribing(false);
    stopPlayback();
  }, [activeSessionId]); // Switches must not put a transcript or audio playback in another conversation.

  useEffect(() => () => {
    transcriptionAbortRef.current?.abort();
    stopPlayback();
  }, [stopPlayback]);

  const handleStartRecording = async () => {
    try {
      await recorder.start();
    } catch (error) {
      toast({
        variant: "destructive",
        title: language === "fr" ? "Microphone indisponible" : "الميكروفون غير متاح",
        description: error instanceof Error ? error.message : undefined,
      });
    }
  };

  const handleStopRecording = async () => {
    setIsTranscribing(true);
    const controller = new AbortController();
    transcriptionAbortRef.current = controller;
    try {
      const file = await recorder.stop();
      if (controller.signal.aborted) return;
      const text = await transcribeVoice(file, language, controller.signal);
      if (!controller.signal.aborted) setMessageInput((previous) => [previous.trim(), text].filter(Boolean).join(" "));
    } catch (error) {
      if (!controller.signal.aborted) {
        toast({
          variant: "destructive",
          title: language === "fr" ? "Transcription impossible" : "تعذر تحويل الصوت إلى نص",
          description: error instanceof Error ? error.message : undefined,
        });
      }
    } finally {
      if (transcriptionAbortRef.current === controller) {
        transcriptionAbortRef.current = null;
        setIsTranscribing(false);
      }
    }
  };

  const { data: sessions = [], isSuccess: sessionsLoaded } = useQuery({
    queryKey: ["chat-sessions"],
    queryFn: listChatSessions,
  });
  const { data: messages = [] } = useQuery({
    queryKey: ["chat-messages", activeSessionId],
    queryFn: () => listSessionMessages(activeSessionId),
    enabled: Boolean(activeSessionId),
  });
  const sendChatMessage = useMutation({
    mutationFn: (content: string) =>
      sendSessionMessage(activeSessionId, content, language as "ar" | "fr" | "darija"),
    onMutate: (content: string) => {
      // Optimistically show user message immediately
      setPendingUserMsg({
        id: `pending-${Date.now()}`,
        role: "user",
        content,
        createdAt: new Date().toISOString(),
      });
    },
    onSettled: () => {
      setPendingUserMsg(null);
    },
  });

  const deleteSessionMutation = useMutation({
    mutationFn: deleteChatSession,
    onSuccess: (_, deletedSessionId) => {
      queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
      if (activeSessionId === deletedSessionId) {
        setActiveSessionId(""); // It will auto-select the first one if available via useEffect
      }
      toast({
        title: language === "fr" ? "Session supprimée" : "تم حذف الجلسة",
        description: language === "fr" ? "La conversation a été supprimée." : "تم حذف المحادثة بنجاح.",
      });
    },
    onError: (err) => {
      toast({
        variant: "destructive",
        title: language === "fr" ? "Erreur" : "خطأ",
        description: err instanceof Error ? err.message : String(err),
      });
    }
  });

  useEffect(() => {
    if (sessionsLoaded && !activeSessionId) {
      setActiveSessionId(sessions[0]?.id ?? crypto.randomUUID());
    }
  }, [sessions, sessionsLoaded, activeSessionId]);

  const handleNewConversation = useCallback(() => {
    setActiveSessionId(crypto.randomUUID());
    setMessageInput("");
    setStagedFile(null);
    setPendingUserMsg(null);
  }, []);

  // Combine persisted messages + optimistic pending user message
  const displayMessages: ChatMessage[] = [
    ...(messages ?? []),
    ...(pendingUserMsg ? [pendingUserMsg] : []),
  ];

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [displayMessages, sendChatMessage.isPending, isUploading]);

  const handleFileSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;

    const reason = validateFile(file);
    if (reason) {
      toast({
        variant: "destructive",
        title: language === "fr" ? "Fichier refusé" : "الملف مرفوض",
        description:
          reason === "too_large"
            ? (language === "fr" ? "Taille maximale : 10 MB." : "الحجم الأقصى: 10 ميغابايت.")
            : (language === "fr" ? "Formats acceptés : PDF, JPEG, PNG, WebP." : "الصيغ المقبولة: PDF, JPEG, PNG, WebP."),
      });
      return;
    }

    // Stage file for preview / attachment and run smart extraction
    setStagedFile(file);
    setExtractedDoc(null);
    setIsAnalyzingDoc(true);

    try {
      const metadata = await analyzeAndExtractDocument(file, language);
      setExtractedDoc(metadata);
    } catch (err) {
      console.warn("Document analysis notice:", err);
    } finally {
      setIsAnalyzingDoc(false);
    }
  };

  const handlePreFillRequest = (fields: {
    applicantName: string;
    cinNumber: string;
    address: string;
    birthDate: string;
    documentType: string;
  }) => {
    try {
      sessionStorage.setItem("omniagent_prefill", JSON.stringify(fields));
      toast({
        title: language === "fr" ? "Données pré-remplies !" : "تم حفظ البيانات!",
        description:
          language === "fr"
            ? "Redirection vers le formulaire de démarche administrative..."
            : "جاري توجيهك إلى استمارة الإجراء الإداري...",
      });
      setLocation("/services?prefill=true");
    } catch (err) {
      console.error("Failed to store prefill:", err);
    }
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = messageInput.trim();
    const fileToSend = stagedFile;

    if (!trimmed && !fileToSend) return;
    if (sendChatMessage.isPending || isUploading) return;

    // Reset inputs immediately for snappy UX
    setMessageInput("");
    setStagedFile(null);
    setExtractedDoc(null);

    // Case 1: An attachment is present (with or without accompanying text)
    if (fileToSend) {
      setIsUploading(true);
      const userDisplayMsg = trimmed
        ? `${DOCUMENT_PREFIX}${fileToSend.name}\n\n${trimmed}`
        : `${DOCUMENT_PREFIX}${fileToSend.name}`;

      setPendingUserMsg({
        id: `pending-${Date.now()}`,
        role: "user",
        content: userDisplayMsg,
        createdAt: new Date().toISOString(),
      });

      try {
        await uploadChatDocument(fileToSend, language, activeSessionId, trimmed);
        queryClient.invalidateQueries({ queryKey: ["chat-messages", activeSessionId] });
        queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
      } catch (err) {
        toast({
          variant: "destructive",
          title: language === "fr" ? "Échec de l'envoi" : "فشل الإرسال",
          description: err instanceof Error ? err.message : undefined,
        });
        // Restore input state on error
        setStagedFile(fileToSend);
        setMessageInput(trimmed);
      } finally {
        setPendingUserMsg(null);
        setIsUploading(false);
      }
      return;
    }

    // Case 2: Text-only message
    sendChatMessage.mutate(trimmed, {
      onSettled: () => {
        queryClient.invalidateQueries({ queryKey: ["chat-messages", activeSessionId] });
        queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
      },
      onError: (err) => {
        toast({
          variant: "destructive",
          title: language === "fr" ? "Erreur" : "خطأ",
          description: err instanceof Error ? err.message : String(err),
        });
        // Re-populate input so user can retry
        setMessageInput(trimmed);
      },
    });
  };

  const prompts = language === "fr"
    ? [
        "Comment renouveler ma carte d'identité (CIN) ?",
        "Quels documents pour un certificat de résidence ?",
        "Quel est le délai final pour déclarer le décès ?",
        "Combien coûte l'extrait de casier judiciaire ?",
      ] 
    : language === "ar"
    ? [
        "كيف أجدد بطاقة التعريف الوطنية؟",
        "ما هي وثائق شهادة السكنى؟",
        "كم الأجل للتصريح بالوفاة؟",
        "كم رسوم السجل العدلي؟",
      ]
    : [
        "كيفاش نجدد لاكارط ناسيونال (CIN)؟",
        "شنو الوثائق باش نخرج شهادة السكنى؟",
        "شنو هي المدة القانونية باش نيلغ على الوفاة؟",
        "شحال ديال الوقت باش يخرج السجل العدلي؟",
      ];

  const todayStart = new Date();
  todayStart.setHours(0, 0, 0, 0);
  const yesterdayStart = new Date(todayStart);
  yesterdayStart.setDate(yesterdayStart.getDate() - 1);
  const historyGroups = [
    { label: language === "fr" ? "Aujourd'hui" : "اليوم", items: sessions.filter((session) => new Date(session.updatedAt) >= todayStart) },
    { label: language === "fr" ? "Hier" : "أمس", items: sessions.filter((session) => new Date(session.updatedAt) >= yesterdayStart && new Date(session.updatedAt) < todayStart) },
    { label: language === "fr" ? "Plus ancien" : "الأقدم", items: sessions.filter((session) => !(new Date(session.updatedAt) >= yesterdayStart)) },
  ];
  const activeSession = sessions.find((session) => session.id === activeSessionId);

  const historyList = (
    <div className="space-y-6">
      {historyGroups.filter((group) => group.items.length > 0).map((group) => (
        <div key={group.label}>
          <h3 className="mb-2 px-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">{group.label}</h3>
          <div className="space-y-2">
            {group.items.map((session) => (
              <div
                key={session.id}
                className={`group relative flex min-w-0 items-center rounded-xl border bg-card transition-colors ${
                  activeSessionId === session.id
                    ? "border-primary/50 bg-primary/[0.06]"
                    : "border-border hover:border-primary/25 hover:bg-muted/35"
                }`}
              >
                <button
                  type="button"
                  onClick={() => { setActiveSessionId(session.id); setHistoryOpen(false); }}
                  className={`flex min-w-0 flex-1 items-center gap-3 px-3 py-3 ${isRtl ? "text-right" : "text-left"}`}
                  aria-current={activeSessionId === session.id ? "page" : undefined}
                  aria-label={language === "fr" ? `Ouvrir la conversation ${session.title}` : `فتح المحادثة ${session.title}`}
                >
                  <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border ${activeSessionId === session.id ? "border-primary/30 bg-primary/10 text-primary" : "border-border bg-muted/40 text-muted-foreground"}`}>
                    <MessageSquare className="h-4 w-4" />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span dir="auto" className={`block truncate text-sm text-foreground ${activeSessionId === session.id ? "font-semibold" : "font-medium"}`}>{session.title}</span>
                    <span className="mt-0.5 block text-[11px] text-muted-foreground">{new Date(session.updatedAt).toLocaleDateString(language === "fr" ? "fr-FR" : "ar-MA", { day: "2-digit", month: "short", year: "numeric" })}</span>
                  </span>
                </button>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="me-2 h-8 w-8 shrink-0 rounded-lg text-muted-foreground opacity-70 hover:bg-background hover:opacity-100 focus-visible:opacity-100" aria-label={language === "fr" ? `Options pour ${session.title}` : `خيارات ${session.title}`}>
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align={isRtl ? "start" : "end"}>
                    <DropdownMenuItem aria-label={language === "fr" ? `Supprimer la conversation ${session.title}` : `حذف المحادثة ${session.title}`} disabled={deleteSessionMutation.isPending} onSelect={() => { setHistoryOpen(false); setSessionToDelete(session.id); }} className="gap-2 text-destructive focus:text-destructive">
                      <Trash2 className="h-4 w-4" />
                      {language === "fr" ? "Supprimer" : "حذف"}
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            ))}
          </div>
        </div>
      ))}
      {!sessions.length && <p className="px-2 py-6 text-center text-sm text-muted-foreground">{language === "fr" ? "Aucune ancienne conversation." : "لا توجد محادثات سابقة."}</p>}
    </div>
  );

  return (
    <AppLayout fullHeight>
      <div className="flex h-full min-h-0 w-full min-w-0 flex-col gap-2 bg-background sm:gap-3">
        <div className="flex shrink-0 items-center justify-between gap-2 rounded-xl border border-border bg-card px-3 py-2 sm:gap-3 sm:px-5 sm:py-3 lg:px-6">
          <div className="min-w-0">
            <h1 className="text-lg font-bold text-[#17365d] dark:text-foreground sm:text-xl">{t("nav.chat")}</h1>
            <p className="hidden text-xs text-muted-foreground sm:block">{language === "fr" ? "Information et accompagnement pour vos démarches administratives" : "المعلومات والمواكبة في إجراءاتك الإدارية"}</p>
          </div>
          <div className="flex shrink-0 items-center gap-2 lg:hidden">
            <Button
              variant="outline"
              size="sm"
              className="h-9 gap-1.5"
              onClick={() => setHistoryOpen(true)}
              aria-label={language === "fr" ? "Ouvrir l'historique" : "فتح سجل المحادثات"}
            >
              <History className="h-4 w-4" />
              <span className="hidden sm:inline">{language === "fr" ? "Historique" : "سجل المحادثات"}</span>
            </Button>
            <Button variant="outline" size="icon" className="h-9 w-9" onClick={handleNewConversation} aria-label={language === "fr" ? "Nouvelle discussion" : "محادثة جديدة"}>
              <MessageSquarePlus className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="flex min-h-0 min-w-0 flex-1 gap-3 overflow-hidden">
          <aside className="hidden min-h-0 w-[288px] shrink-0 flex-col overflow-hidden rounded-xl border border-border bg-card lg:flex xl:w-[320px] 2xl:w-[336px]" aria-label={language === "fr" ? "Historique des conversations" : "سجل المحادثات"}>
            <div className="shrink-0 border-b border-border px-4 py-4">
              <div className="mb-3 flex items-center gap-2">
                <History className="h-4 w-4 text-primary" />
                <h2 className="text-xs font-semibold uppercase tracking-[0.1em] text-[#17365d] dark:text-foreground">{language === "fr" ? "Historique des conversations" : "سجل المحادثات"}</h2>
              </div>
              <Button size="sm" className="w-full justify-start gap-2 rounded-lg" onClick={handleNewConversation} data-testid="button-new-conversation" aria-label={language === "fr" ? "Créer une nouvelle conversation" : "إنشاء محادثة جديدة"}>
                <MessageSquarePlus className="h-4 w-4" />
                {language === "fr" ? "Nouvelle conversation" : "محادثة جديدة"}
              </Button>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto p-3">{historyList}</div>
          </aside>

          <section className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden rounded-xl border border-border bg-muted/20" aria-label={language === "fr" ? "Conversation" : "المحادثة"}>
            <header className="flex shrink-0 items-center justify-between gap-3 border-b border-border bg-card px-3 py-2.5 sm:px-5 sm:py-3">
              <div className="min-w-0">
                <h2 dir="auto" className="truncate text-sm font-semibold text-[#17365d] dark:text-foreground">
                  {activeSession?.title || (language === "fr" ? "Nouvelle conversation" : "محادثة جديدة")}
                </h2>
                <p className="truncate text-xs text-muted-foreground">{language === "fr" ? "Assistant administratif numérique · Sources documentaires vérifiées" : "مساعد إداري رقمي · مصادر وثائقية موثوقة"}</p>
              </div>
            </header>
            <ScrollArea className="min-h-0 flex-1" viewportRef={scrollRef}>
              <div className="space-y-3 px-3 py-3 sm:space-y-5 sm:px-5 sm:py-5 lg:px-6">
                {!displayMessages.length && !sendChatMessage.isPending && (
                  <div className="mx-auto w-full max-w-3xl px-1 py-2 text-center sm:py-8">
                    {/* Assistant Avatar Badge */}
                    <div className="mx-auto mb-3 flex h-11 w-11 items-center justify-center rounded-lg border border-primary/20 bg-primary/5 text-primary">
                      <Landmark className="h-5 w-5" />
                    </div>

                    {/* Structured Welcome Title */}
                    <h2 className="mb-2 text-lg font-semibold leading-snug text-foreground sm:text-xl">
                      {language === "fr"
                        ? "Bonjour, comment puis-je vous accompagner ?"
                        : language === "ar"
                        ? "مرحباً، كيف يمكنني مساعدتك؟"
                        : "السلام عليكم، كيفاش نقدر نعاونك؟"}
                    </h2>

                    {/* Structured Description */}
                    <p className="mx-auto mb-3 max-w-lg text-sm leading-relaxed text-muted-foreground sm:mb-5">
                      {language === "fr"
                        ? "Je peux vous orienter dans vos démarches, vérifier la conformité de vos pièces jointes ou suivre l'état d'avancement de vos dossiers."
                        : language === "ar"
                        ? "يمكنني إرشادك في إجراءاتك الإدارية، التحقق من مطابقة وثائقك المرفقة، أو تتبع حالة تقدم ملفاتك."
                        : "نقدر نعاونك ونوجهك في جميع الإجراءات الإدارية، نتحقق من الوثائق ديالك، ولا نتبعو حالة الملفات ديالك."}
                    </p>

                    {/* 3 Structured Capabilities */}
                    <div className="mb-4 grid grid-cols-1 gap-2 text-start sm:mb-6 sm:grid-cols-3" dir={isRtl ? "rtl" : "ltr"}>
                      <div className="rounded-md border border-border bg-muted/20 p-2.5 sm:p-3">
                        <div className="mb-2 flex h-7 w-7 items-center justify-center rounded-md bg-primary/5 text-primary">
                          <Compass className="w-4 h-4" />
                        </div>
                        <h3 className="text-xs font-semibold text-foreground mb-1">
                          {language === "fr" ? "Orientation démarches" : "توجيه الإجراءات"}
                        </h3>
                        <p className="text-[11px] text-muted-foreground leading-relaxed">
                          {language === "fr" ? "Guide étape par étape pour vos formalités (CIN, actes...)" : "دليل مفصل للمساطر الإدارية والوثائق"}
                        </p>
                      </div>

                      <div className="rounded-md border border-border bg-muted/20 p-2.5 sm:p-3">
                        <div className="mb-2 flex h-7 w-7 items-center justify-center rounded-md bg-primary/5 text-primary">
                          <FileCheck2 className="w-4 h-4" />
                        </div>
                        <h3 className="text-xs font-semibold text-foreground mb-1">
                          {language === "fr" ? "Conformité des pièces" : "التحقق من الوثائق"}
                        </h3>
                        <p className="text-[11px] text-muted-foreground leading-relaxed">
                          {language === "fr" ? "Vérification des pièces requises et formats" : "فحص مطابقة الملفات والصيغ المطلوبة"}
                        </p>
                      </div>

                      <div className="rounded-md border border-border bg-muted/20 p-2.5 sm:p-3">
                        <div className="mb-2 flex h-7 w-7 items-center justify-center rounded-md bg-primary/5 text-primary">
                          <FolderClock className="w-4 h-4" />
                        </div>
                        <h3 className="text-xs font-semibold text-foreground mb-1">
                          {language === "fr" ? "Suivi des dossiers" : "تتبع الملفات"}
                        </h3>
                        <p className="text-[11px] text-muted-foreground leading-relaxed">
                          {language === "fr" ? "Statuts, délais estimés et étapes en cours" : "متابعة تقدم الطلبات والآجال المتبقية"}
                        </p>
                      </div>
                    </div>

                    {/* Suggestions Section on Welcome Screen */}
                    <div id="questions-frequentes" className="space-y-2.5 text-start" dir={isRtl ? "rtl" : "ltr"}>
                      <div className="text-xs font-medium text-muted-foreground flex items-center gap-1.5 px-1">
                        <Sparkles className="w-3.5 h-3.5 text-primary" />
                        <span>{language === "fr" ? "Exemples de questions fréquentes :" : "أمثلة على الأسئلة الشائعة:"}</span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {prompts.map((p, i) => (
                          <button
                            key={i}
                            type="button"
                            onClick={() => setMessageInput(p)}
                            className="group flex items-center justify-between rounded-md border border-border bg-card p-2.5 text-start text-xs font-medium text-foreground transition-colors hover:border-primary/40 hover:bg-primary/5"
                          >
                            <span className="truncate flex-1">{p}</span>
                            <ArrowUpRight className="w-3.5 h-3.5 text-muted-foreground group-hover:text-primary transition-colors shrink-0 ml-2" />
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
                {displayMessages.map((msg) => (
                  <div key={msg.id} className={`flex min-w-0 gap-2 sm:gap-3 ${msg.role === 'user' ? 'max-w-[96%] sm:max-w-[76%] xl:max-w-[70%]' : 'max-w-[98%] sm:max-w-[84%] xl:max-w-[78%]'} ${msg.role === 'user' ? (isRtl ? 'mr-auto flex-row-reverse' : 'ml-auto flex-row-reverse') : (isRtl ? 'ml-auto' : 'mr-auto')}`}>
                    <div className={`flex h-8 w-8 sm:h-9 sm:w-9 shrink-0 items-center justify-center rounded-lg border ${msg.role === 'user' ? 'border-[#17365d] bg-[#17365d] text-white' : 'border-primary/25 bg-card text-primary'}`}>
                      {msg.role === 'user' ? <User className="h-4 w-4 sm:h-[18px] sm:w-[18px]" /> : <Landmark className="h-4 w-4 sm:h-[18px] sm:w-[18px]" />}
                    </div>
                    <div className={`min-w-0 break-words rounded-xl border px-3 py-2 text-xs leading-relaxed sm:px-5 sm:py-4 sm:text-sm ${msg.role === 'user' ? 'border-[#17365d] bg-[#17365d] text-white' : 'border-border bg-card text-card-foreground'}`}>
                      <ChatMessageContent
                        content={msg.content}
                        role={msg.role as "user" | "assistant"}
                        isRtl={isRtl}
                      />
                      {msg.role === "assistant" && (
                        <button
                          type="button"
                          onClick={() => void playMessage(msg)}
                          className="mt-2 inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs text-primary hover:bg-primary/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                          aria-label={playback?.messageId === String(msg.id)
                            ? (language === "fr" ? "Arrêter la lecture" : "إيقاف القراءة")
                            : (language === "fr" ? "Écouter la réponse" : "استمع إلى الرد")}
                          aria-pressed={playback?.messageId === String(msg.id)}
                        >
                          {playback?.messageId === String(msg.id) && playback.state === "loading"
                            ? <Loader2 className="h-4 w-4 animate-spin" />
                            : playback?.messageId === String(msg.id)
                            ? <Square className="h-4 w-4 fill-current" />
                            : <Volume2 className="h-4 w-4" />}
                          <span>{playback?.messageId === String(msg.id)
                            ? (language === "fr" ? "Arrêter" : "إيقاف")
                            : (language === "fr" ? "Écouter" : "استمع")}</span>
                        </button>
                      )}
                      {/* RAG metadata for assistant messages */}
                      {msg.role === 'assistant' && (msg.confidence != null || (msg.sources && msg.sources.length > 0)) && (
                        <div className="mt-3 pt-2 border-t border-border/40 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-muted-foreground">
                          {msg.confidence != null && (
                            <span className="inline-flex items-center gap-1">
                              <ShieldCheck className="w-3 h-3" />
                              {language === "fr" ? "Confiance" : "الثقة"}: {Math.round(msg.confidence * 100)}%
                            </span>
                          )}
                          {msg.sources && msg.sources.length > 0 && (
                            <span className="inline-flex items-center gap-1">
                              <BookOpen className="w-3 h-3" />
                              {msg.sources.join(", ")}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {sendChatMessage.isPending && (
                  <div className={`flex max-w-[94%] gap-2.5 sm:max-w-[84%] sm:gap-3 xl:max-w-[78%] ${isRtl ? 'ml-auto' : 'mr-auto'}`}>
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-primary/25 bg-card text-primary">
                      <Landmark className="h-[18px] w-[18px]" />
                    </div>
                    <div className="flex items-center gap-2 rounded-xl border border-border bg-card px-4 py-3 text-sm">
                      <span className="w-2 h-2 bg-primary/50 rounded-full animate-bounce"></span>
                      <span className="w-2 h-2 bg-primary/50 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></span>
                      <span className="w-2 h-2 bg-primary/50 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></span>
                    </div>
                  </div>
                )}
                {Boolean(displayMessages.length) && !sendChatMessage.isPending && (
                  <div id="questions-frequentes" className="max-w-2xl pt-2">
                    <p className="mb-2 text-xs font-medium text-muted-foreground">{t("chat.suggested")}</p>
                    <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                      {prompts.map((prompt, index) => (
                        <button key={index} type="button" onClick={() => setMessageInput(prompt)} className="truncate rounded-md border bg-card px-3 py-2 text-start text-xs text-foreground transition-colors hover:border-primary/40 hover:bg-primary/5">
                          {prompt}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>
            
            <div className="flex max-h-[50%] min-h-0 shrink-0 flex-col border-t border-border bg-card px-3 py-3 sm:px-5">
              <div className="min-h-0 overflow-y-auto">
              {/* ── Feature 2: Document Scanning Skeleton or Extracted Document Card ── */}
              {isAnalyzingDoc && stagedFile ? (
                <div className="mb-3">
                  <DocumentScanningSkeleton
                    filename={stagedFile.name}
                    isRtl={isRtl}
                    language={language}
                  />
                </div>
              ) : stagedFile && extractedDoc ? (
                <div className="mb-3">
                  <ExtractedDocumentCard
                    metadata={extractedDoc}
                    file={stagedFile}
                    onPreFillRequest={handlePreFillRequest}
                    onSendToChat={() => void handleSendMessage()}
                    onDismiss={() => {
                      setStagedFile(null);
                      setExtractedDoc(null);
                    }}
                  />
                </div>
              ) : stagedFile ? (
                <div
                  className={`mb-3 flex items-center justify-between gap-3 rounded-xl border border-primary/25 bg-primary/10 p-3 animate-in fade-in slide-in-from-bottom-2 duration-150 ${
                    isRtl ? "flex-row-reverse" : ""
                  }`}
                >
                  <div
                    className={`flex items-center gap-3 min-w-0 flex-1 ${
                      isRtl ? "flex-row-reverse text-right" : "text-left"
                    }`}
                  >
                    <div className="w-10 h-10 rounded-xl bg-primary/20 text-primary flex items-center justify-center shrink-0">
                      {stagedFile.type.startsWith("image/") ? (
                        <ImageIcon className="w-5 h-5" />
                      ) : (
                        <FileText className="w-5 h-5" />
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div
                        className="text-xs sm:text-sm font-semibold text-foreground truncate"
                        title={stagedFile.name}
                      >
                        {stagedFile.name}
                      </div>
                      <div className="text-[11px] text-muted-foreground flex items-center gap-1.5 mt-0.5">
                        <span>{formatFileSize(stagedFile.size)}</span>
                        <span>•</span>
                        <span className="text-primary font-medium">
                          {language === "fr"
                            ? "Pièce jointe prête (cliquez sur Envoyer)"
                            : "مرفق جاهز (اضغط على إرسال)"}
                        </span>
                      </div>
                    </div>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 rounded-lg text-muted-foreground hover:text-destructive hover:bg-destructive/10 shrink-0"
                    onClick={() => {
                      setStagedFile(null);
                      setExtractedDoc(null);
                    }}
                    title={language === "fr" ? "Supprimer la pièce jointe" : "إلغاء المرفق"}
                  >
                    <X className="w-4 h-4" />
                    <span className="sr-only">Cancel</span>
                  </Button>
                </div>
              ) : null}
              </div>
              {recorder.status !== "idle" || isTranscribing ? (
                <div className="flex items-center gap-3 rounded-xl border border-destructive/30 bg-destructive/5 p-2 min-h-14" role="status" aria-live="polite">
                  <span className={`h-3 w-3 shrink-0 rounded-full bg-destructive ${recorder.status === "recording" ? "animate-pulse" : ""}`} aria-hidden="true" />
                  <span className="flex-1 text-sm font-medium">
                    {isTranscribing
                      ? (language === "fr" ? "Transcription en cours…" : "جاري تحويل الصوت إلى نص…")
                      : recorder.status === "requesting"
                      ? (language === "fr" ? "Autorisation du microphone…" : "جاري طلب إذن الميكروفون…")
                      : recorder.status === "stopping"
                      ? (language === "fr" ? "Préparation de l'audio…" : "جاري تجهيز الصوت…")
                      : `${language === "fr" ? "Enregistrement" : "تسجيل"}  ${String(Math.floor(recorder.duration / 60)).padStart(2, "0")}:${String(recorder.duration % 60).padStart(2, "0")}`}
                  </span>
                  {!isTranscribing && (
                    <Button type="button" variant="ghost" size="icon" onClick={recorder.cancel}
                      title={language === "fr" ? "Annuler l'enregistrement" : "إلغاء التسجيل"}
                      aria-label={language === "fr" ? "Annuler l'enregistrement" : "إلغاء التسجيل"}>
                      <X className="h-5 w-5" />
                    </Button>
                  )}
                  {recorder.status === "recording" && (
                    <Button type="button" onClick={() => void handleStopRecording()} className="gap-2 rounded-lg"
                      aria-label={language === "fr" ? "Arrêter et transcrire" : "إيقاف التسجيل وتحويله إلى نص"}>
                      <Square className="h-4 w-4 fill-current" />
                      {language === "fr" ? "Terminer" : "إنهاء"}
                    </Button>
                  )}
                  {isTranscribing && <Loader2 className="h-5 w-5 animate-spin text-primary" aria-hidden="true" />}
                </div>
              ) : <form onSubmit={handleSendMessage} className="flex shrink-0 items-center gap-0.5 rounded-xl border border-border bg-background p-1 sm:p-1.5 sm:gap-1">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="application/pdf,image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={handleFileSelected}
                  data-testid="input-chat-file"
                />
                <Button
                  type="button"
                  variant={stagedFile ? "secondary" : "outline"}
                  size="icon"
                  className={`h-8 w-8 shrink-0 rounded-md border-0 shadow-none sm:h-10 sm:w-10 ${
                    stagedFile ? "text-primary border-primary/40 bg-primary/10" : "text-muted-foreground"
                  }`}
                  disabled={isUploading}
                  onClick={() => fileInputRef.current?.click()}
                  aria-label={
                    stagedFile
                      ? (language === "fr" ? "Changer la pièce jointe" : "تغيير المرفق")
                      : (language === "fr" ? "Joindre un document" : "إرفاق وثيقة")
                  }
                  title={
                    stagedFile
                      ? (language === "fr" ? "Changer la pièce jointe" : "تغيير المرفق")
                      : (language === "fr" ? "Joindre un document" : "إرفاق وثيقة")
                  }
                >
                  {isUploading ? <Loader2 className="w-4 h-4 sm:w-5 sm:h-5 animate-spin" /> : <Upload className="w-4 h-4 sm:w-5 sm:h-5" />}
                </Button>
                <Button type="button" variant="ghost" size="icon" className="h-8 w-8 shrink-0 rounded-md text-muted-foreground sm:h-10 sm:w-10"
                  onClick={() => void handleStartRecording()}
                  disabled={isUploading || sendChatMessage.isPending}
                  title={language === "fr" ? "Enregistrer un message vocal" : "تسجيل رسالة صوتية"}
                  aria-label={language === "fr" ? "Enregistrer un message vocal" : "تسجيل رسالة صوتية"}>
                  <Mic className="w-4 h-4 sm:w-5 sm:h-5" />
                </Button>
                <Input 
                  value={messageInput} 
                  onChange={e => setMessageInput(e.target.value)} 
                  placeholder={
                    stagedFile
                      ? (language === "fr" ? "Ajouter un message avec votre document (optionnel)..." : "أضف رسالة مع الوثيقة (اختياري)...")
                      : t("chat.placeholder")
                  }
                  className="h-8 min-w-0 flex-1 border-0 bg-transparent px-1.5 text-sm shadow-none focus-visible:ring-0 sm:h-10 sm:px-3 sm:text-base"
                  aria-label={language === "fr" ? "Votre message" : "رسالتك"}
                />
                <Button 
                  type="submit" 
                  size="icon" 
                  disabled={(!messageInput.trim() && !stagedFile) || sendChatMessage.isPending || isUploading} 
                  className="h-8 w-8 shrink-0 rounded-md bg-primary text-white transition-colors hover:bg-primary/90 disabled:opacity-50 sm:h-10 sm:w-10"
                  title={language === "fr" ? "Envoyer" : "إرسال"}
                  aria-label={language === "fr" ? "Envoyer le message" : "إرسال الرسالة"}
                >
                  {isUploading || sendChatMessage.isPending ? (
                    <Loader2 className="w-4 h-4 sm:w-5 sm:h-5 animate-spin" />
                  ) : (
                    <Send className={`w-4 h-4 sm:w-5 sm:h-5 ${isRtl ? 'rotate-180' : ''}`} />
                  )}
                </Button>
              </form>}
            </div>
          </section>
        </div>
      </div>

      <Sheet open={historyOpen} onOpenChange={setHistoryOpen}>
        <SheetContent side={isRtl ? "right" : "left"} className="flex h-full w-[min(88vw,340px)] flex-col gap-0 overflow-hidden p-0 lg:hidden" dir={isRtl ? "rtl" : "ltr"}>
          <SheetHeader className="shrink-0 border-b px-4 py-5 text-start">
            <SheetTitle className="text-sm">{language === "fr" ? "Historique des conversations" : "سجل المحادثات"}</SheetTitle>
          </SheetHeader>
          <div className="shrink-0 border-b p-3">
            <Button size="sm" className="w-full justify-start gap-2 rounded-lg" onClick={() => { handleNewConversation(); setHistoryOpen(false); }} aria-label={language === "fr" ? "Créer une nouvelle conversation" : "إنشاء محادثة جديدة"}>
              <MessageSquarePlus className="h-4 w-4" />{language === "fr" ? "Nouvelle conversation" : "محادثة جديدة"}
            </Button>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto p-2.5">{historyList}</div>
        </SheetContent>
      </Sheet>

      <AlertDialog open={Boolean(sessionToDelete)} onOpenChange={(open) => !open && setSessionToDelete(null)}>
        <AlertDialogContent className="max-w-md rounded-xl border bg-card p-6 shadow-lg">
          <AlertDialogHeader className={`space-y-3 ${isRtl ? "text-right" : "text-left"}`}>
            <div className={`flex items-center gap-3.5 ${isRtl ? "flex-row-reverse" : ""}`}>
              <div className="w-12 h-12 rounded-full bg-destructive/10 text-destructive flex items-center justify-center shrink-0">
                <Trash2 className="w-6 h-6" />
              </div>
              <div>
                <AlertDialogTitle className="text-lg font-semibold text-foreground">
                  {language === "fr" ? "Supprimer cette discussion ?" : "واش بصح بغيتي تمسح هاد المحادثة؟"}
                </AlertDialogTitle>
                <AlertDialogDescription className="text-sm text-muted-foreground mt-1">
                  {language === "fr"
                    ? "Cette action est irréversible. L'ensemble des messages de cette discussion sera définitivement effacé."
                    : "هاد العملية نهائية وما يمكنش ترجع فيها. كاع الرسائل ديال هاد المحادثة غادي يتمسحو."}
                </AlertDialogDescription>
              </div>
            </div>
          </AlertDialogHeader>
          <AlertDialogFooter className={`mt-6 gap-2 sm:gap-0 ${isRtl ? "sm:flex-row-reverse sm:space-x-reverse" : ""}`}>
            <AlertDialogCancel
              disabled={deleteSessionMutation.isPending}
              className="rounded-xl border-border hover:bg-muted font-medium"
            >
              {language === "fr" ? "Annuler" : "إلغاء"}
            </AlertDialogCancel>
            <AlertDialogAction
              className="rounded-xl bg-destructive hover:bg-destructive/90 text-destructive-foreground font-medium shadow-sm transition-all"
              disabled={deleteSessionMutation.isPending}
              onClick={(e) => {
                e.preventDefault();
                if (sessionToDelete) {
                  const id = sessionToDelete;
                  setSessionToDelete(null);
                  deleteSessionMutation.mutate(id);
                }
              }}
            >
              {deleteSessionMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                language === "fr" ? "Supprimer" : "مسح"
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </AppLayout>
  );
}
