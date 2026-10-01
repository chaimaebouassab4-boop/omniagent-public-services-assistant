/** Persistent standalone-chat API backed by SQLAlchemy and the RAG service. */
import { apiUrl } from "@/lib/api-url";
import { getToken, handleUnauthorized } from "@/lib/auth";
import type { Language } from "@/lib/i18n";

export interface ChatMessage {
  id: string | number;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
  confidence?: number;
  sources?: string[];
  fallbackReason?: string;
  conversationState?: ConversationState | null;
  chunks?: { content: string; metadata: Record<string, unknown>; similarity_score: number }[];
}

export interface ConversationState {
  session_id: string;
  current_procedure_id: string | null;
  current_procedure_title: string | null;
  user_type: string | null;
  stage: "exploring" | "procedure_identified" | "collecting_info" | "ready";
  last_user_intent: string | null;
  mentioned_documents: string[];
  special_case: string | null;
  language: "fr" | "ar" | "darija";
  turn_count: number;
  last_updated: string;
}

export function getConversationState(sessionId: string): Promise<ConversationState> {
  return chatFetch<ConversationState>(`/api/chat/sessions/${encodeURIComponent(sessionId)}/state`);
}

export interface ChatSession {
  id: string;
  title: string;
  preview: string;
  messageCount: number;
  createdAt: string;
  updatedAt: string;
  messages?: ChatMessage[];
}

async function chatFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const response = await fetch(apiUrl(path), {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers ?? {}),
    },
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    handleUnauthorized(response.status);
    const detail = data?.detail ?? `Échec de la requête chat (HTTP ${response.status})`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data as T;
}

export function listChatSessions(): Promise<ChatSession[]> {
  return chatFetch<ChatSession[]>("/api/chat/sessions");
}

export function listSessionMessages(sessionId: string): Promise<ChatMessage[]> {
  return chatFetch<ChatMessage[]>(
    `/api/chat/messages?sessionId=${encodeURIComponent(sessionId)}`,
  );
}

export async function sendSessionMessage(
  sessionId: string,
  content: string,
  language: "ar" | "fr" | "darija",
): Promise<{ userMessage: ChatMessage; assistantMessage: ChatMessage }> {
  const userMessage: ChatMessage = {
    id: `pending-${crypto.randomUUID()}`,
    role: "user",
    content,
    createdAt: new Date().toISOString(),
  };
  const assistantMessage = await chatFetch<ChatMessage>("/api/chat/messages", {
    method: "POST",
    body: JSON.stringify({ content, language, sessionId }),
  });
  return { userMessage, assistantMessage };
}

export async function deleteChatSession(sessionId: string): Promise<void> {
  await chatFetch<{ deleted: number }>(
    `/api/chat/sessions/${encodeURIComponent(sessionId)}`,
    { method: "DELETE" },
  );
}

export async function clearChatHistory(): Promise<number> {
  const result = await chatFetch<{ deleted: number }>("/api/chat/messages", {
    method: "DELETE",
  });
  return result.deleted;
}

async function voiceError(response: Response): Promise<Error> {
  const data = await response.json().catch(() => null);
  handleUnauthorized(response.status);
  const detail = data?.detail ?? `Erreur audio (HTTP ${response.status})`;
  return new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
}

export async function transcribeVoice(file: File, language: Language, signal?: AbortSignal): Promise<string> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("language", language);
  const token = getToken();
  const response = await fetch(apiUrl("/api/chat/voice-transcribe"), {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    body: formData,
    signal,
  });
  if (!response.ok) throw await voiceError(response);
  const data = await response.json() as { text?: string; error?: string };
  if (data.error) throw new Error(data.error);
  if (!data.text?.trim()) throw new Error("Aucune parole reconnue dans l'enregistrement.");
  return data.text.trim();
}

export async function synthesizeVoice(text: string, language: Language, signal?: AbortSignal): Promise<Blob> {
  const token = getToken();
  const response = await fetch(apiUrl("/api/chat/voice-synthesize"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ text, language }),
    signal,
  });
  if (!response.ok) throw await voiceError(response);
  return response.blob();
}
