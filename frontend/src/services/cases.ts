import { cases } from "../data/mockData";
import { apiClient } from "./apiClient";
import type { ApiSuccess, CreateCasePayload, PublicCase } from "../types/api";

/** Creates a new citizen case through the backend API. */
export async function createCase(payload: CreateCasePayload): Promise<PublicCase> {
  const response = await apiClient.post<ApiSuccess<PublicCase>>("/api/cases", payload);
  return response.data.data;
}

/** Loads a case by id, falling back to local seed data during API bring-up. */
export async function getCase(id: string): Promise<PublicCase> {
  try {
    const response = await apiClient.get<ApiSuccess<PublicCase>>(`/api/cases/${id}`);
    return response.data.data;
  } catch {
    const fallback = cases.find((item) => item.id === id) ?? cases[0];
    return Promise.resolve(fallback);
  }
}

/** Returns case rows for citizen and admin list screens. */
export async function listCases(): Promise<PublicCase[]> {
  return Promise.resolve(cases);
}

/** Uploads one document for a case. */
export async function uploadCaseDocument(caseId: string, file: File): Promise<void> {
  const formData = new FormData();
  formData.append("file", file);
  await apiClient.post(`/api/cases/${caseId}/upload`, formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
}

/** Approves a submitted case. */
export async function approveCase(caseId: string): Promise<void> {
  await apiClient.post(`/api/admin/approve/${caseId}`);
}

/** Rejects a submitted case with an optional reviewer reason. */
export async function rejectCase(caseId: string, reason: string): Promise<void> {
  await apiClient.post(`/api/admin/reject/${caseId}`, { reason });
}
