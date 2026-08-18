/**
 * Local stub for @workspace/api-client-react
 * Replaces the Replit monorepo package with direct fetch calls to our FastAPI backend.
 */
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getToken } from "@/lib/auth";
import { apiUrl } from "@/lib/api-url";

// ─── Auth token getter ────────────────────────────────────────────────────────
let _tokenGetter: () => string | null = () => getToken();

export function setAuthTokenGetter(fn: () => string | null) {
  _tokenGetter = fn;
}

// ─── Base fetch helper ────────────────────────────────────────────────────────
async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = _tokenGetter();
  const res = await fetch(apiUrl(path), {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers ?? {}),
    },
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const msg =
      (data && (data.detail || data.message)) || "Une erreur est survenue";
    const err: any = new Error(typeof msg === "string" ? msg : "Erreur");
    err.status = res.status;
    throw err;
  }
  return data as T;
}

// ─── Types ────────────────────────────────────────────────────────────────────
export interface Service {
  id: number;
  nameFr: string;
  nameAr: string;
  descriptionFr: string;
  descriptionAr: string;
  processingDays: number;
  requiredDocuments: string[] | null;
}

export interface Case {
  id: number;
  referenceNumber: string;
  status: string;
  applicantName: string;
  applicantEmail: string;
  applicantPhone?: string;
  notes?: string;
  submittedAt: string;
  service?: Service;
}

export interface TimelineEvent {
  id: number;
  descriptionFr: string;
  descriptionAr: string;
  occurredAt: string;
}

export interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
}

export interface Document {
  id: number;
  name: string;
  fileSize: number;
  status: "pending" | "verified" | "rejected";
  uploadedAt: string;
}

export interface DashboardSummary {
  activeCases: number;
  pendingDocuments: number;
  avgProcessingDays: number;
  approvedCases: number;
  recentCases: Case[];
}

export interface AdminStats {
  totalCases: number;
  casesByStatus: { status: string; count: number }[];
  casesByService: { serviceNameFr: string; count: number }[];
}

// ─── Query key factories ──────────────────────────────────────────────────────
export const getListMessagesQueryKey = (caseId: number) => ["messages", caseId];
export const getListDocumentsQueryKey = (caseId: number) => ["documents", caseId];
export const getAdminListCasesQueryKey = () => ["admin", "cases"];
export const getGetAdminStatsQueryKey = () => ["admin", "stats"];

// ─── Services ─────────────────────────────────────────────────────────────────
export function useListServices() {
  return useQuery<Service[]>({
    queryKey: ["services"],
    queryFn: () => apiFetch("/api/services"),
  });
}

// ─── Cases ────────────────────────────────────────────────────────────────────
export function useCreateCase() {
  return useMutation<Case, Error, { data: { serviceId: number; applicantName: string; applicantEmail: string; applicantPhone?: string; notes?: string } }>({
    mutationFn: ({ data }) =>
      apiFetch("/api/cases", { method: "POST", body: JSON.stringify(data) }),
  });
}

export function useGetCase(caseId: number, options?: any) {
  return useQuery<Case>({
    queryKey: ["case", caseId],
    queryFn: () => apiFetch(`/api/cases/${caseId}`),
    enabled: !!caseId,
    ...options?.query,
  });
}

export function useGetCaseTimeline(caseId: number, options?: any) {
  return useQuery<TimelineEvent[]>({
    queryKey: ["case-timeline", caseId],
    queryFn: () => apiFetch(`/api/cases/${caseId}/timeline`),
    enabled: !!caseId,
    ...options?.query,
  });
}

// ─── Messages ─────────────────────────────────────────────────────────────────
export function useListMessages(caseId: number, options?: any) {
  return useQuery<Message[]>({
    queryKey: getListMessagesQueryKey(caseId),
    queryFn: () => apiFetch(`/api/cases/${caseId}/messages`),
    enabled: !!caseId,
    ...options?.query,
  });
}

export function useSendMessage() {
  return useMutation<Message, Error, { id: number; data: { content: string; language: string } }>({
    mutationFn: ({ id, data }) =>
      apiFetch(`/api/cases/${id}/messages`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
  });
}

// ─── Documents ────────────────────────────────────────────────────────────────
export function useListDocuments(caseId: number, options?: any) {
  return useQuery<Document[]>({
    queryKey: getListDocumentsQueryKey(caseId),
    queryFn: () => apiFetch(`/api/cases/${caseId}/documents`),
    enabled: !!caseId,
    ...options?.query,
  });
}

// ─── Dashboard ────────────────────────────────────────────────────────────────
export function useGetDashboardSummary() {
  return useQuery<DashboardSummary>({
    queryKey: ["dashboard"],
    queryFn: () => apiFetch("/api/dashboard/summary"),
  });
}

// ─── Admin ────────────────────────────────────────────────────────────────────
export function useGetAdminStats() {
  return useQuery<AdminStats>({
    queryKey: getGetAdminStatsQueryKey(),
    queryFn: () => apiFetch("/api/admin/stats"),
  });
}

export function useAdminListCases() {
  return useQuery<Case[]>({
    queryKey: getAdminListCasesQueryKey(),
    queryFn: () => apiFetch("/api/admin/cases"),
  });
}

export function useUpdateCase() {
  return useMutation<Case, Error, { id: number; data: { status: string } }>({
    mutationFn: ({ id, data }) =>
      apiFetch(`/api/admin/cases/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
  });
}
