import { useI18n } from "@/lib/i18n";
import { AppLayout } from "@/components/layout/AppLayout";
import { useListChatMessages, useSendChatMessage, getListChatMessagesQueryKey } from "@workspace/api-client-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Upload, Mic, Send, Bot, User, FileText, Loader2, MessageSquarePlus } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";
import { uploadChatDocument, validateFile } from "@/lib/documents";
import { clearChatHistory } from "@/lib/chat";

const DOCUMENT_PREFIX = "[Document] ";

export default function Chat() {
  const { t, language, isRtl } = useI18n();
  const { data: messages } = useListChatMessages();
  const sendChatMessage = useSendChatMessage();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [messageInput, setMessageInput] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleNewConversation = async () => {
    if (!messages?.length) return;
    const confirmText = language === "fr"
      ? "Commencer une nouvelle discussion ? L'historique actuel sera effacé."
      : "بغيتي تبدا محادثة جديدة؟ غادي يتمسح السجل الحالي.";
    if (!window.confirm(confirmText)) return;

    setIsClearing(true);
    try {
      await clearChatHistory();
      queryClient.invalidateQueries({ queryKey: getListChatMessagesQueryKey() });
      toast({
        title: language === "fr" ? "Nouvelle discussion" : "محادثة جديدة",
        description: language === "fr" ? "L'historique a été effacé." : "تم مسح السجل.",
      });
    } catch (err) {
      toast({
        variant: "destructive",
        title: language === "fr" ? "Échec" : "فشل",
        description: err instanceof Error ? err.message : undefined,
      });
    } finally {
      setIsClearing(false);
    }
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, sendChatMessage.isPending, isUploading]);

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
      await uploadChatDocument(file, language);
      queryClient.invalidateQueries({ queryKey: getListChatMessagesQueryKey() });
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
    if (!messageInput.trim()) return;

    sendChatMessage.mutate(
      { data: { content: messageInput, language: language as "ar"|"fr"|"darija" } },
      {
        onSuccess: () => {
          setMessageInput("");
          queryClient.invalidateQueries({ queryKey: getListChatMessagesQueryKey() });
        }
      }
    );
  };

  const prompts = language === "fr" 
    ? ["Comment renouveler ma carte d'identité ?", "Quels documents pour un certificat de résidence ?", "Où trouver une licence commerciale ?"] 
    : ["كيفاش نجدد بطاقة التعريف؟", "شنو هي الوثائق اللي خصني نجيب لشهادة السكنى؟", "بغيت نسول على رخصة تجارية"];

  return (
    <AppLayout>
      <div className="max-w-4xl mx-auto h-[calc(100vh-80px)] flex flex-col">
        <div className={`mb-4 shrink-0 flex items-center justify-between ${isRtl ? "flex-row-reverse" : ""}`}>
          <h1 className="text-3xl font-bold text-foreground">{t("nav.chat")}</h1>
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5"
            disabled={isClearing || !messages?.length}
            onClick={handleNewConversation}
            data-testid="button-new-conversation"
          >
            {isClearing ? <Loader2 className="w-4 h-4 animate-spin" /> : <MessageSquarePlus className="w-4 h-4" />}
            {language === "fr" ? "Nouvelle discussion" : "محادثة جديدة"}
          </Button>
        </div>

        <Card className="flex-1 flex flex-col min-h-0 overflow-hidden shadow-sm">
          <CardContent className="flex-1 flex flex-col p-0 overflow-hidden bg-muted/10">
            <ScrollArea className="flex-1 p-6" viewportRef={scrollRef}>
              <div className="space-y-6">
                {!messages?.length && (
                  <div className="text-center text-muted-foreground mt-20">
                    <Bot className="w-12 h-12 mx-auto mb-4 text-primary opacity-50" />
                    <p>{language === "fr" ? "Bonjour! Comment puis-je vous aider aujourd'hui?" : "مرحباً! كيفاش نقدر نعاونك اليوم؟"}</p>
                  </div>
                )}
                {messages?.map((msg) => (
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
    </AppLayout>
  );
}
