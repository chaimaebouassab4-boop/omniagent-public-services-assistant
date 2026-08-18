import { apiUrl } from "@/lib/api-url";
import { getToken, handleUnauthorized } from "@/lib/auth";

export interface VisitEntry {
  id: string;
  page: string;
  pageLabel: string;
  timestamp: number;
  duration?: number;
  lang: string;
}

export interface VisitorEntry extends VisitEntry {
  sessionId: string;
  device: "Mobile" | "Desktop" | "Tablette";
  city: string;
}

const HISTORY_KEY = "omniagent_history";
const SESSION_KEY = "omniagent_session";

function genId(): string {
  return crypto.randomUUID();
}

function detectDevice(): VisitorEntry["device"] {
  const agent = navigator.userAgent.toLowerCase();
  if (/ipad|tablet/.test(agent)) return "Tablette";
  if (/android|iphone|mobile/.test(agent)) return "Mobile";
  return "Desktop";
}

export function trackVisit(page: string, pageLabel: string, lang: string): void {
  const history: VisitEntry[] = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
  history.unshift({ id: genId(), page, pageLabel, timestamp: Date.now(), lang });
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, 100)));

  const sessionId = localStorage.getItem(SESSION_KEY) || genId();
  localStorage.setItem(SESSION_KEY, sessionId);
  void fetch(apiUrl("/api/analytics/visits"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sessionId, page, pageLabel, language: lang, device: detectDevice() }),
  }).catch(() => {
    // Analytics must never interrupt normal navigation.
  });
}

export function getHistory(): VisitEntry[] {
  return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
}

export function clearHistory(): void {
  localStorage.removeItem(HISTORY_KEY);
}

export async function getVisitors(): Promise<VisitorEntry[]> {
  const token = getToken();
  const response = await fetch(apiUrl("/api/admin/analytics/visits"), {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (!response.ok) {
    handleUnauthorized(response.status);
    throw new Error(`Analytics request failed (HTTP ${response.status})`);
  }
  return response.json();
}
