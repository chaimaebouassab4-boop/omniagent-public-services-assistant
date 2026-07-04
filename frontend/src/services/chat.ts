import { messages } from "../data/mockData";
import { apiClient } from "./apiClient";
import type { ChatMessage } from "../types/api";

const wsBaseURL = import.meta.env.VITE_WS_BASE_URL ?? "ws://localhost:8000";

/** Creates the WebSocket URL for a case chat channel. */
export function getChatSocketUrl(caseId: string): string {
  return `${wsBaseURL}/ws/chat/${caseId}`;
}

/** Loads starter chat messages until the WebSocket backend is enabled. */
export async function listMessages(caseId: string): Promise<ChatMessage[]> {
  return Promise.resolve(messages.filter((message) => message.caseId === caseId));
}

interface SendChatPayload {
  serviceId: string;
  message: string;
  language?: string;
}

interface SendChatResponse {
  status: "success";
  data: {
    response: string;
    message_id: string;
    service_id: string;
  };
}

/** Sends message to backend knowledge base endpoint and returns assistant reply. */
export async function sendChatMessage(payload: SendChatPayload): Promise<string> {
  const response = await apiClient.post<SendChatResponse>("/api/chat", {
    service_id: payload.serviceId,
    message: payload.message,
    language: payload.language ?? "darija"
  }, {
    headers: {
      "X-Skip-Auth": "true"
    }
  });
  return response.data.data.response;
}
