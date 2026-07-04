export type CaseStatus = "Submitted" | "Approved" | "Rejected";

export type ServiceType = "licence" | "permit" | "residence" | "birth" | "marriage";

export interface ApiSuccess<T> {
  data: T;
  status: "success";
}

export interface ApiErrorBody {
  error: string;
  code: number;
}

export interface User {
  id: string;
  email: string;
  isAdmin: boolean;
}

export interface AuthTokens {
  accessToken: string;
  tokenType: "bearer";
}

export interface Service {
  id: ServiceType;
  name: string;
  description: string;
  requiredDocuments: string[];
  averageProcessingDays: number;
}

export interface Document {
  id: string;
  caseId: string;
  fileName: string;
  filePath: string;
  uploadedAt: string;
}

export interface AuditLog {
  id: string;
  caseId: string;
  action: "created" | "uploaded" | "approved" | "rejected" | "commented";
  actorId: string;
  timestamp: string;
}

export interface PublicCase {
  id: string;
  userId: string;
  serviceType: ServiceType;
  status: CaseStatus;
  createdAt: string;
  updatedAt: string;
  applicantName: string;
  referenceNumber: string;
  documents: Document[];
  timeline: AuditLog[];
}

export interface ChatMessage {
  id: string;
  caseId: string;
  sender: "citizen" | "assistant" | "admin";
  body: string;
  createdAt: string;
  status?: "sending" | "sent" | "read";
  pending?: boolean;
}

export interface CreateCasePayload {
  serviceType: ServiceType;
  applicantName: string;
  email: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}
