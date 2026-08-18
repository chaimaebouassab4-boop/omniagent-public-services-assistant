import { useI18n } from "@/lib/i18n";
import { AppLayout } from "@/components/layout/AppLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Upload, Mic, Send, Bot, User, FileText, Loader2, MessageSquarePlus, History, BookOpen, ShieldCheck } from "lucide-react";
import { useState, useRef, useEffect, useCallback } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";
import { uploadChatDocument, validateFile } from "@/lib/documents";
import { listChatSessions, listSessionMessages, sendSessionMessage } from "@/lib/chat";
import type { ChatMessage } from "@/lib/chat";

const DOCUMENT_PREFIX = "[Document] ";

export default function Chat() {
  const { t, language, isRtl } = useI18n();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [activeSessionId, setActiveSessionId] = useState("");
  const [messageInput, setMessageInput] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  /** Optimistic messages shown while waiting for RAG response */
  const [pendingUserMsg, setPendingUserMsg] = useState<ChatMessage | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  useEffect(() => {
    if (sessionsLoaded && !activeSessionId) {
      setActiveSessionId(sessions[0]?.id ?? crypto.randomUUID());
    }
  }, [sessions, sessionsLoaded, activeSessionId]);

  const handleNewConversation = useCallback(() => {
    setActiveSessionId(crypto.randomUUID());
    setMessageInput("");
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

    setIsUploading(true);
    try {
      await uploadChatDocument(file, language, activeSessionId);
      queryClient.invalidateQueries({ queryKey: ["chat-messages", activeSessionId] });
      queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
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

  const handleSendMessage = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = messageInput.trim();
    if (!trimmed) return;

    // Clear input immediately for snappy UX
    setMessageInput("");

    sendChatMessage.mutate(trimmed, {
      onSettled: () => {
        // Always refresh caches — the user message was already saved to
        // localStorage before the API call, so it should show regardless.
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
    ? ["Comment renouveler ma carte d'identité ?", "Quels documents pour un certificat de résidence ?", "Où trouver une licence commerciale ?"] 
    : ["كيفاش نجدد بطاقة التعريف؟", "شنو هي الوثائق اللي خصني نجيب لشهادة السكنى؟", "بغيت نسول على رخصة تجارية"];

  return (
    <AppLayout>
      <div className="max-w-6xl mx-auto h-[calc(100vh-80px)] flex flex-col">
        <div className={`mb-4 shrink-0 flex items-center justify-between ${isRtl ? "flex-row-reverse" : ""}`}>
          <h1 className="text-3xl font-bold text-foreground">{t("nav.chat")}</h1>
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5"
            onClick={handleNewConversation}
            data-testid="button-new-conversation"
          >
            <MessageSquarePlus className="w-4 h-4" />
            {language === "fr" ? "Nouvelle discussion" : "محادثة جديدة"}
          </Button>
        </div>

        <div className="flex-1 min-h-0 grid gap-4 md:grid-cols-[260px_minmax(0,1fr)]">
          <Card className="flex max-h-44 min-h-0 flex-col overflow-hidden md:max-h-none">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <History className="w-4 h-4" />
                {language === "fr" ? "Historique" : "سجل المحادثات"}
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 min-h-0 overflow-y-auto px-3 pb-3">
              <div className="space-y-2">
                {sessions.map((session) => (
                  <button
                    key={session.id}
                    type="button"
                    onClick={() => setActiveSessionId(session.id)}
                    className={`w-full rounded-lg border p-3 text-left transition-colors ${
                      activeSessionId === session.id
                        ? "border-primary bg-primary/10"
                        : "hover:bg-muted"
                    }`}
                  >
                    <div className="truncate text-sm font-medium">{session.title}</div>
                    <div className="mt-1 truncate text-xs text-muted-foreground">
                      {session.preview}
                    </div>
                    <div className="mt-2 text-[11px] text-muted-foreground">
                      {new Date(session.updatedAt).toLocaleDateString(
                        language === "fr" ? "fr-FR" : "ar-MA",
                      )}
                    </div>
                  </button>
                ))}
                {!sessions.length && (
                  <p className="py-6 text-center text-sm text-muted-foreground">
                    {language === "fr" ? "Aucune ancienne conversation." : "لا توجد محادثات سابقة."}
                  </p>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="flex flex-col min-h-0 overflow-hidden shadow-sm">
          <CardContent className="flex-1 flex flex-col p-0 overflow-hidden bg-muted/10">
            <ScrollArea className="flex-1 p-6" viewportRef={scrollRef}>
              <div className="space-y-6">
                {!displayMessages.length && !sendChatMessage.isPending && (
                  <div className="text-center text-muted-foreground mt-20">
                    <Bot className="w-12 h-12 mx-auto mb-4 text-primary opacity-50" />
                    <p>{language === "fr" ? "Bonjour! Comment puis-je vous aider aujourd'hui?" : "مرحباً! كيفاش نقدر نعاونك اليوم؟"}</p>
                  </div>
                )}
                {displayMessages.map((msg) => (
                  <div key={msg.id} className={`flex gap-4 max-w-[85%] ${msg.role === 'user' ? (isRtl ? 'mr-auto flex-row-reverse' : 'ml-auto flex-row-reverse') : (isRtl ? 'ml-auto' : 'mr-auto')}`}>
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-sm ${msg.role === 'user' ? 'bg-secondary text-white' : 'bg-primary text-white'}`}>
                      {msg.role === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
                    </div>
                    <div className={`p-4 rounded-2xl text-sm leading-relaxed shadow-sm ${msg.role === 'user' ? 'bg-secondary text-white rounded-tr-none' : 'bg-card border rounded-tl-none text-card-foreground'}`}>
                      {msg.content.startsWith(DOCUMENT_PREFIX) ? (
                        <span className="inline-flex items-center gap-2 font-medium">
                          <FileText className="w-4 h-4 shrink-0" />
                          {msg.content.slice(DOCUMENT_PREFIX.length)}
                        </span>
                      ) : (
                        msg.content
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
                  <div className={`flex gap-4 max-w-[85%] ${isRtl ? 'ml-auto' : 'mr-auto'}`}>
                    <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-sm bg-primary text-white">
                      <Bot className="w-5 h-5" />
                    </div>
                    <div className="p-4 rounded-2xl text-sm bg-card border rounded-tl-none flex items-center gap-2">
                      <span className="w-2 h-2 bg-primary/50 rounded-full animate-bounce"></span>
                      <span className="w-2 h-2 bg-primary/50 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></span>
                      <span className="w-2 h-2 bg-primary/50 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></span>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>
            
            <div className="p-6 border-t bg-card shrink-0">
              <div className="mb-4">
                <div className="text-xs font-medium text-muted-foreground mb-2">{t("chat.suggested")}</div>
                <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
                  {prompts.map((p, i) => (
                    <button 
                      key={i} 
                      onClick={() => setMessageInput(p)}
                      className="whitespace-nowrap px-4 py-2 bg-muted hover:bg-muted/80 text-sm rounded-full border transition-colors"
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
              <form onSubmit={handleSendMessage} className="flex gap-3">
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
                  variant="outline"
                  size="icon"
                  className="shrink-0 w-12 h-12 rounded-xl text-muted-foreground"
                  disabled={isUploading}
                  onClick={() => fileInputRef.current?.click()}
                  title={language === "fr" ? "Joindre un document" : "إرفاق وثيقة"}
                >
                  {isUploading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Upload className="w-5 h-5" />}
                </Button>
                <Button type="button" variant="outline" size="icon" className="shrink-0 w-12 h-12 rounded-xl text-muted-foreground">
                  <Mic className="w-5 h-5" />
                </Button>
                <Input 
                  value={messageInput} 
                  onChange={e => setMessageInput(e.target.value)} 
                  placeholder={t("chat.placeholder")}
                  className="flex-1 h-12 rounded-xl text-base px-4 bg-muted/50 focus-visible:bg-background"
                />
                <Button type="submit" size="icon" disabled={!messageInput.trim() || sendChatMessage.isPending} className="shrink-0 w-12 h-12 rounded-xl bg-primary hover:bg-primary/90 text-white">
                  <Send className={`w-5 h-5 ${isRtl ? 'rotate-180' : ''}`} />
                </Button>
              </form>
            </div>
          </CardContent>
          </Card>
        </div>
      </div>
    </AppLayout>
  );
}
