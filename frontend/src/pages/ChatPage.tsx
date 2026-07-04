import { AnimatePresence, motion } from "framer-motion";
import { Moon, ShieldCheck, Sun, Wifi, WifiOff } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import toast, { Toaster } from "react-hot-toast";
import { useParams } from "react-router-dom";
import { ChatInput } from "../components/chat/ChatInput";
import { ChatMessage } from "../components/chat/ChatMessage";
import { LoadingSkeletons } from "../components/chat/LoadingSkeletons";
import { ProgressTimeline } from "../components/chat/ProgressTimeline";
import { TypingIndicator } from "../components/chat/TypingIndicator";
import { Card, CardContent, CardHeader } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { useWebSocket } from "../hooks/useWebSocket";
import { listMessages, sendChatMessage } from "../services/chat";
import { useChatStore } from "../store/chatStore";
import type { ChatMessage as ChatMessageType, ServiceType } from "../types/api";
import { cn } from "../lib/utils";

/** Real-time-ready case chat screen with backend KB responses. */
export function ChatPage(): JSX.Element {
  const { serviceId = "licence" } = useParams<{ serviceId: ServiceType }>();
  const [darkMode, setDarkMode] = useState(false);
  const messages = useChatStore((state) => state.messages);
  const isTyping = useChatStore((state) => state.isTyping);
  const isConnected = useChatStore((state) => state.isConnected);
  const isLoading = useChatStore((state) => state.isLoading);
  const hydrateMessages = useChatStore((state) => state.hydrateMessages);
  const addMessage = useChatStore((state) => state.addMessage);
  const markMessageRead = useChatStore((state) => state.markMessageRead);
  const setLoading = useChatStore((state) => state.setLoading);
  const setTyping = useChatStore((state) => state.setTyping);
  const messagesContainerRef = useRef<HTMLDivElement | null>(null);

  const serviceSteps = useMemo(
    () => [
      { title: "Chat demarre", description: "Lmo3awin waslak daba.", completed: true },
      { title: "Watha2iq", description: "Khass tkamal files mtloba.", completed: false },
      { title: "Moraja3a idariya", description: "Talab ghadi ymchi lmoqata3a.", completed: false }
    ],
    []
  );

  useWebSocket({ caseId: serviceId });

  useEffect(() => {
    setLoading(true);
    listMessages("7f4b6c9d-7a65-4b18-b551-e94db6c49a01")
      .then((loaded) =>
        hydrateMessages(
          loaded.map((message) => ({
            ...message,
            status: message.sender === "citizen" ? "read" : "sent",
            pending: false
          }))
        )
      )
      .finally(() => setLoading(false));
  }, [hydrateMessages, setLoading]);

  useEffect(() => {
    if (!messagesContainerRef.current) {
      return;
    }
    messagesContainerRef.current.scrollTo({
      top: messagesContainerRef.current.scrollHeight,
      behavior: "smooth"
    });
  }, [messages, isTyping]);

  function resolveServiceId(routeServiceId: string): string {
    const map: Record<string, string> = {
      birth: "birth_certificate",
      residence: "residence_certificate",
      marriage: "marriage_contract"
    };
    return map[routeServiceId] ?? routeServiceId;
  }

  function handleSendMessage(body: string): void {
    const outgoing: ChatMessageType = {
      id: crypto.randomUUID(),
      caseId: "7f4b6c9d-7a65-4b18-b551-e94db6c49a01",
      sender: "citizen",
      body,
      createdAt: new Date().toISOString(),
      pending: true,
      status: "sending"
    };

    addMessage(outgoing);
    toast.success("Message envoye");
    setTyping(true);

    window.setTimeout(async () => {
      try {
        const backendReply = await sendChatMessage({
          serviceId: resolveServiceId(serviceId),
          message: body,
          language: "darija"
        });

        addMessage({
          id: crypto.randomUUID(),
          caseId: outgoing.caseId,
          sender: "assistant",
          body: backendReply,
          createdAt: new Date().toISOString(),
          status: "sent",
          pending: false
        });
      } catch {
        addMessage({
          id: crypto.randomUUID(),
          caseId: outgoing.caseId,
          sender: "assistant",
          body: "Ma l9it-sh lbackend dyal lchat daba. Chghal server w 3awed jarrab.",
          createdAt: new Date().toISOString(),
          status: "sent",
          pending: false
        });
        toast.error("Chat backend offline");
      } finally {
        markMessageRead(outgoing.id);
        setTyping(false);
      }
    }, 700);
  }

  return (
    <div className={cn(darkMode && "dark")}>
      <Toaster position="bottom-right" />
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
        <Card className="min-h-[calc(100vh-150px)] overflow-hidden border-[#d9ccb8] bg-white dark:border-slate-700 dark:bg-slate-900">
          <CardHeader className="flex flex-row items-center justify-between gap-3 bg-gradient-to-r from-[#fffdf8] to-[#eef8f8] p-6 dark:from-slate-900 dark:to-slate-800">
            <div className="flex items-center gap-4">
              <motion.span
                animate={isConnected ? { scale: [1, 1.06, 1] } : { scale: 1 }}
                transition={{ duration: 1.8, repeat: Number.POSITIVE_INFINITY }}
                className="grid h-12 w-12 place-items-center rounded-xl bg-[#0f3d5e] text-white shadow-sm"
              >
                <ShieldCheck className="h-6 w-6" aria-hidden="true" />
              </motion.span>
              <div>
                <h1 className="text-2xl font-extrabold capitalize text-slate-950 dark:text-slate-50">
                  {serviceId} Assistant
                </h1>
                <p className="mt-1 text-sm font-medium text-slate-500 dark:text-slate-300">
                  Secure case-aware chat channel
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setDarkMode((current) => !current)}
                className="rounded-lg border border-[#d9ccb8] bg-white p-2 text-slate-600 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                aria-label="Toggle dark mode"
              >
                {darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              </button>
              <Badge
                className={cn(
                  "hidden gap-1 sm:inline-flex",
                  isConnected ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"
                )}
              >
                {isConnected ? (
                  <Wifi className="h-3.5 w-3.5" aria-hidden="true" />
                ) : (
                  <WifiOff className="h-3.5 w-3.5" aria-hidden="true" />
                )}
                {isConnected ? "Connected" : "Offline mode"}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="grid h-[calc(100vh-244px)] min-h-[560px] grid-rows-[1fr_auto] gap-4 bg-slate-50/70 p-5 dark:bg-slate-900/70">
            <div
              ref={messagesContainerRef}
              className="space-y-4 overflow-y-auto rounded-xl border border-[#d9ccb8] bg-[linear-gradient(180deg,#fffdf8,#ffffff)] p-4 shadow-inner dark:border-slate-700 dark:bg-[linear-gradient(180deg,#0f172a,#111827)]"
              aria-live="polite"
            >
              {isLoading ? <LoadingSkeletons /> : null}
              <AnimatePresence>
                {!isLoading
                  ? messages.map((message, index) => (
                      <ChatMessage key={message.id} message={message} index={index} />
                    ))
                  : null}
              </AnimatePresence>
              <AnimatePresence>{isTyping ? <TypingIndicator /> : null}</AnimatePresence>
            </div>
            <ChatInput onSend={handleSendMessage} />
          </CardContent>
        </Card>
        <aside className="grid content-start gap-4">
          <motion.div initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }}>
            <Card className="overflow-hidden border-[#d9ccb8] bg-white dark:border-slate-700 dark:bg-slate-900">
              <CardHeader className="bg-white p-5 dark:bg-slate-900">
                <h2 className="font-extrabold text-slate-950 dark:text-slate-100">Case summary</h2>
              </CardHeader>
              <CardContent className="grid gap-4">
                <div className="grid gap-3">
                  <div className="flex items-center justify-between rounded-lg bg-[#fff8ef] p-3 dark:bg-slate-800">
                    <span className="text-sm font-semibold text-slate-500">Service</span>
                    <span className="text-sm font-bold capitalize text-slate-950 dark:text-slate-100">{serviceId}</span>
                  </div>
                  <div className="flex items-center justify-between rounded-lg bg-[#fff8ef] p-3 dark:bg-slate-800">
                    <span className="text-sm font-semibold text-slate-500">Status</span>
                    <Badge className="bg-amber-100 text-amber-800">Draft</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.06 }}>
            <Card className="overflow-hidden border-[#d9ccb8] bg-white dark:border-slate-700 dark:bg-slate-900">
              <CardHeader>
                <h2 className="font-extrabold text-slate-950 dark:text-slate-100">Progress</h2>
              </CardHeader>
              <CardContent>
                <ProgressTimeline steps={serviceSteps} />
              </CardContent>
            </Card>
          </motion.div>
        </aside>
      </div>
    </div>
  );
}
