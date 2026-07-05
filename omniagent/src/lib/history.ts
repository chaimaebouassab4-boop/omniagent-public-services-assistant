export interface VisitEntry {
  id: string;
  page: string;
  pageLabel: string;
  timestamp: number;
  duration?: number;
  lang: string;
}

export interface VisitorEntry {
  id: string;
  sessionId: string;
  page: string;
  pageLabel: string;
  timestamp: number;
  device: string;
  city: string;
  lang: string;
}

const HISTORY_KEY = "omniagent_history";
const VISITORS_KEY = "omniagent_visitors";

function genId() {
  return Math.random().toString(36).slice(2, 10);
}

const CITIES = ["Casablanca", "Rabat", "Marrakech", "Fès", "Tanger", "Agadir", "Oujda", "Meknès", "Laâyoune", "Tétouan"];
const DEVICES = ["Mobile", "Desktop", "Tablette"];

export function trackVisit(page: string, pageLabel: string, lang: string) {
  const history: VisitEntry[] = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
  const entry: VisitEntry = {
    id: genId(),
    page,
    pageLabel,
    timestamp: Date.now(),
    lang,
  };
  history.unshift(entry);
  if (history.length > 100) history.pop();
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history));

  const visitors: VisitorEntry[] = JSON.parse(localStorage.getItem(VISITORS_KEY) || "[]");
  const sessionId = localStorage.getItem("omniagent_session") || genId();
  localStorage.setItem("omniagent_session", sessionId);
  const vEntry: VisitorEntry = {
    id: genId(),
    sessionId,
    page,
    pageLabel,
    timestamp: Date.now(),
    device: DEVICES[Math.floor(Math.random() * DEVICES.length)],
    city: CITIES[Math.floor(Math.random() * CITIES.length)],
    lang,
  };
  visitors.unshift(vEntry);
  if (visitors.length > 200) visitors.pop();
  localStorage.setItem(VISITORS_KEY, JSON.stringify(visitors));
}

export function getHistory(): VisitEntry[] {
  return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
}

export function clearHistory() {
  localStorage.removeItem(HISTORY_KEY);
}

export function getVisitors(): VisitorEntry[] {
  return JSON.parse(localStorage.getItem(VISITORS_KEY) || "[]");
}

export function seedVisitors() {
  const existing = getVisitors();
  if (existing.length > 10) return;

  const pages = [
    { page: "/", label: "Accueil" },
    { page: "/services", label: "Services" },
    { page: "/chat", label: "Assistant IA" },
    { page: "/login", label: "Connexion" },
    { page: "/signup", label: "Inscription" },
    { page: "/services/1", label: "CIN" },
    { page: "/services/2", label: "Passeport" },
  ];
  const langs = ["fr", "ar", "darija"];
  const now = Date.now();
  const seed: VisitorEntry[] = Array.from({ length: 48 }, (_, i) => {
    const p = pages[Math.floor(Math.random() * pages.length)];
    return {
      id: genId(),
      sessionId: genId(),
      page: p.page,
      pageLabel: p.label,
      timestamp: now - Math.floor(Math.random() * 7 * 24 * 3600 * 1000),
      device: DEVICES[Math.floor(Math.random() * DEVICES.length)],
      city: CITIES[Math.floor(Math.random() * CITIES.length)],
      lang: langs[Math.floor(Math.random() * langs.length)],
    };
  });
  seed.sort((a, b) => b.timestamp - a.timestamp);
  localStorage.setItem(VISITORS_KEY, JSON.stringify(seed));
}
