/**
 * Document upload helper.
 *
 * The generated API client has no multipart hook, so uploads go through a
 * plain fetch with FormData. The Bearer token is attached manually, matching
 * the behaviour of the generated client's auth getter.
 */
import { getToken, type AuthUser } from "@/lib/auth";
import type { Document, Message } from "@workspace/api-client-react";

export const MAX_UPLOAD_BYTES = 10 * 1024 * 1024; // keep in sync with backend
export const ALLOWED_UPLOAD_TYPES = [
  "application/pdf",
  "image/jpeg",
  "image/png",
  "image/webp",
];
export const CIN_UPLOAD_TYPES = ["application/pdf", "image/png"];

export function validateFile(file: File, allowedTypes: string[] = ALLOWED_UPLOAD_TYPES): string | null {
  if (!allowedTypes.includes(file.type)) {
    return "invalid_type";
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    return "too_large";
  }
  return null;
}

async function postMultipart<T>(path: string, formData: FormData): Promise<T> {
  const token = getToken();
  const response = await fetch(path, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    body: formData,
  });

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data && typeof data.detail === "string" ? data.detail : null;
    throw new Error(detail ?? `Upload failed (HTTP ${response.status})`);
  }
  return data as T;
}

export async function uploadDocument(
  caseId: number,
  file: File,
  docType = "other",
): Promise<Document> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("docType", docType);
  return postMultipart<Document>(`/api/cases/${caseId}/documents`, formData);
}

/** Uploads the national identity card (PNG/PDF); returns the refreshed profile. */
export async function uploadProfileCin(file: File): Promise<AuthUser> {
  const formData = new FormData();
  formData.append("file", file);
  return postMultipart<AuthUser>("/api/users/me/documents/cin", formData);
}

/** Attaches a personal document to the profile; returns the refreshed profile. */
export async function uploadPersonalDocument(file: File): Promise<AuthUser> {
  const formData = new FormData();
  formData.append("file", file);
  return postMultipart<AuthUser>("/api/users/me/documents/personal", formData);
}

/** Sends a document into the standalone chat; returns the assistant acknowledgement. */
export async function uploadChatDocument(file: File, language = "darija"): Promise<Message> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("language", language);
  return postMultipart<Message>("/api/chat/documents", formData);
}
