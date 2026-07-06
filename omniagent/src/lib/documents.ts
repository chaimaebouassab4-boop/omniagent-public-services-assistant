/**
 * Document upload helper.
 *
 * The generated API client has no multipart hook, so uploads go through a
 * plain fetch with FormData. The Bearer token is attached manually, matching
 * the behaviour of the generated client's auth getter.
 */
import { getToken } from "@/lib/auth";
import type { Document } from "@workspace/api-client-react";

export const MAX_UPLOAD_BYTES = 10 * 1024 * 1024; // keep in sync with backend
export const ALLOWED_UPLOAD_TYPES = [
  "application/pdf",
  "image/jpeg",
  "image/png",
  "image/webp",
];

export function validateFile(file: File): string | null {
  if (!ALLOWED_UPLOAD_TYPES.includes(file.type)) {
    return "invalid_type";
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    return "too_large";
  }
  return null;
}

export async function uploadDocument(
  caseId: number,
  file: File,
  docType = "other",
): Promise<Document> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("docType", docType);

  const token = getToken();
  const response = await fetch(`/api/cases/${caseId}/documents`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    body: formData,
  });

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data && typeof data.detail === "string" ? data.detail : null;
    throw new Error(detail ?? `Upload failed (HTTP ${response.status})`);
  }
  return data as Document;
}
