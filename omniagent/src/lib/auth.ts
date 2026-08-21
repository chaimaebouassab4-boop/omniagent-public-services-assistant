/**
 * Lightweight auth layer for the OmniAgent frontend.
 *
 * Stores the backend-issued JWT in localStorage and exposes helpers for the
 * login / signup / profile pages. The token is attached to every generated
 * API-client request via `setAuthTokenGetter` (wired in App.tsx).
 */
import { apiUrl } from "@/lib/api-url";

const TOKEN_KEY = "omni_token";
const USER_KEY = "omni_user";
const AUTH_ROUTES = new Set(["/login", "/signup"]);

export interface PersonalDocument {
  id: string;
  name: string;
  size: number;
  mimeType: string;
  uploadedAt: string;
}

export interface AuthUser {
  id: string;
  email: string;
  fullName: string;
  phone: string | null;
  isAdmin: boolean;
  notifyEmail?: boolean;
  notifySms?: boolean;
  cinFileName?: string | null;
  personalDocuments?: PersonalDocument[];
}

interface AuthResponse {
  token: string;
  user: AuthUser;
}

export function getToken(): string | null {
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) return null;

  try {
    const payloadPart = token.split(".")[1];
    if (!payloadPart) throw new Error("Malformed JWT");

    const normalized = payloadPart.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
    const payload = JSON.parse(atob(padded)) as { exp?: unknown };

    if (
      typeof payload.exp !== "number" ||
      payload.exp <= Math.floor(Date.now() / 1000)
    ) {
      logout();
      return null;
    }
  } catch {
    logout();
    return null;
  }

  return token;
}

export function getStoredUser(): AuthUser | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function isAuthenticated(): boolean {
  return Boolean(getToken());
}

function persist(token: string, user: AuthUser): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function logout(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/** Clears a rejected session and sends the user to login once. */
export function handleUnauthorized(status: number): boolean {
  if (status !== 401 || !localStorage.getItem(TOKEN_KEY)) return false;

  logout();
  if (!AUTH_ROUTES.has(window.location.pathname)) {
    const returnTo = `${window.location.pathname}${window.location.search}`;
    window.location.assign(`/login?returnTo=${encodeURIComponent(returnTo)}`);
  }
  return true;
}

async function apiRequest<T>(
  path: string,
  method: "GET" | "POST" | "PATCH",
  body?: unknown,
): Promise<T> {
  const token = getToken();
  const response = await fetch(apiUrl(path), {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    handleUnauthorized(response.status);
    const message =
      (data && (data.detail || data.message)) || "Une erreur est survenue";
    throw new Error(typeof message === "string" ? message : "Une erreur est survenue");
  }
  return data as T;
}

export async function login(email: string, password: string): Promise<AuthUser> {
  const data = await apiRequest<AuthResponse>("/api/auth/login", "POST", {
    email,
    password,
  });
  persist(data.token, data.user);
  return data.user;
}

export interface SignupPayload {
  fullName: string;
  email: string;
  phone?: string;
  password: string;
}

export async function signup(payload: SignupPayload): Promise<AuthUser> {
  const data = await apiRequest<AuthResponse>("/api/auth/signup", "POST", payload);
  persist(data.token, data.user);
  return data.user;
}

export async function fetchMe(): Promise<AuthUser> {
  return apiRequest<AuthUser>("/api/auth/me", "GET");
}

export async function updateMe(payload: {
  fullName?: string;
  phone?: string;
  notifyEmail?: boolean;
  notifySms?: boolean;
}): Promise<AuthUser> {
  const user = await apiRequest<AuthUser>("/api/auth/me", "PATCH", payload);
  const token = getToken();
  if (token) persist(token, user);
  return user;
}
