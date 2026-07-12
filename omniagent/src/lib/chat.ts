/** Standalone-chat helpers that fall outside the generated API client. */
import { getToken } from "@/lib/auth";

/** Deletes the current user's standalone chat history; returns the deleted count. */
export async function clearChatHistory(): Promise<number> {
  const token = getToken();
  const response = await fetch("/api/chat/messages", {
    method: "DELETE",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data && typeof data.detail === "string" ? data.detail : null;
    throw new Error(detail ?? `Clear failed (HTTP ${response.status})`);
  }
  return (data && typeof data.deleted === "number" ? data.deleted : 0);
}
