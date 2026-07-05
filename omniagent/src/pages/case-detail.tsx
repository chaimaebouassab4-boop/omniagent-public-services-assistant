import { useI18n } from "@/lib/i18n";
import { AppLayout } from "@/components/layout/AppLayout";
import { useGetCase, useGetCaseTimeline, useListMessages, useSendMessage, getListMessagesQueryKey } from "@workspace/api-client-react";
import { useParams } from "wouter";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "./dashboard";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Upload, Mic, Send, Bot, User, CheckCircle2, Clock } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";

export default function CaseDetail() {
  const { id } = useParams();
  const caseId = parseInt(id || "0", 10);
  const { t, language, isRtl } = useI18n();
  const { data: caseData, isLoading: caseLoading } = useGetCase(caseId, { query: { enabled: !!caseId, queryKey: ['case', caseId] as any } });
  const { data: timeline } = useGetCaseTimeline(caseId, { query: { enabled: !!caseId, queryKey: ['case-timeline', caseId] as any } });
  const { data: messages } = useListMessages(caseId, { query: { enabled: !!caseId, queryKey: getListMessagesQueryKey(caseId) as any } });
  const sendMessage = useSendMessage();
  const queryClient = useQueryClient();

  const [messageInput, setMessageInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

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
                  <Button type="button" variant="outline" size="icon" className="shrink-0 text-muted-foreground">
                    <Upload className="w-4 h-4" />
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
    </AppLayout>
  );
}
