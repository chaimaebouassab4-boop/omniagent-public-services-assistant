/** Standalone-chat helpers that fall outside the generated API client. */
import { getToken, handleUnauthorized } from "@/lib/auth";
import type { Message } from "@workspace/api-client-react";

export interface ChatSession {
  id: string;
  title: string;
  preview: string;
  messageCount: number;
  createdAt: string;
  updatedAt: string;
}

async function chatRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const response = await fetch(path, {
    ...init,
    headers: {
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    handleUnauthorized(response.status);
    throw new Error(data?.detail ?? `Chat request failed (HTTP ${response.status})`);
  }
  return data as T;
}

export function listChatSessions(): Promise<ChatSession[]> {
  return chatRequest<ChatSession[]>("/api/chat/sessions");
}

export function listSessionMessages(sessionId: string): Promise<Message[]> {
  return chatRequest<Message[]>(`/api/chat/messages?sessionId=${encodeURIComponent(sessionId)}`);
}

export function sendSessionMessage(
  sessionId: string,
  content: string,
  language: "ar" | "fr" | "darija",
): Promise<Message> {
  return chatRequest<Message>("/api/chat/messages", {
    method: "POST",
    body: JSON.stringify({ sessionId, content, language }),
  });
}

/** Deletes the current user's standalone chat history; returns the deleted count. */
export async function clearChatHistory(): Promise<number> {
  const token = getToken();
  const response = await fetch("/api/chat/messages", {
    method: "DELETE",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    handleUnauthorized(response.status);
    const detail = data && typeof data.detail === "string" ? data.detail : null;
    throw new Error(detail ?? `Clear failed (HTTP ${response.status})`);
  }
  return (data && typeof data.deleted === "number" ? data.deleted : 0);
}
