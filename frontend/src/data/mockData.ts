import type { ChatMessage, PublicCase, Service } from "../types/api";

const now = new Date().toISOString();

export const services: Service[] = [
  {
    id: "licence",
    name: "Business Licence",
    description: "Apply for or renew a municipal business licence.",
    requiredDocuments: ["CIN copy", "Lease agreement", "Tax certificate"],
    averageProcessingDays: 7
  },
  {
    id: "permit",
    name: "Construction Permit",
    description: "Submit permit requests and track technical review.",
    requiredDocuments: ["CIN copy", "Site plan", "Ownership certificate"],
    averageProcessingDays: 14
  },
  {
    id: "residence",
    name: "Residence Certificate",
    description: "Request proof of residence for official procedures.",
    requiredDocuments: ["CIN copy", "Utility bill"],
    averageProcessingDays: 3
  },
  {
    id: "birth",
    name: "Birth Certificate",
    description: "Request civil registry birth certificate extracts.",
    requiredDocuments: ["Family booklet", "CIN copy"],
    averageProcessingDays: 2
  }
];

export const cases: PublicCase[] = [
  {
    id: "7f4b6c9d-7a65-4b18-b551-e94db6c49a01",
    userId: "9c3d7c4a-7db1-44bd-b21d-1a9d88fbac21",
    serviceType: "licence",
    status: "Submitted",
    createdAt: now,
    updatedAt: now,
    applicantName: "Sara El Idrissi",
    referenceNumber: "CIV-2026-1048",
    documents: [
      {
        id: "doc-1",
        caseId: "7f4b6c9d-7a65-4b18-b551-e94db6c49a01",
        fileName: "cin-copy.pdf",
        filePath: "/uploads/cin-copy.pdf",
        uploadedAt: now
      }
    ],
    timeline: [
      {
        id: "log-1",
        caseId: "7f4b6c9d-7a65-4b18-b551-e94db6c49a01",
        action: "created",
        actorId: "9c3d7c4a-7db1-44bd-b21d-1a9d88fbac21",
        timestamp: now
      }
    ]
  },
  {
    id: "db02aa10-6fd2-4ef6-95cc-5204731858ce",
    userId: "2a99a8ac-c89e-4e62-81db-af51f6500f7f",
    serviceType: "residence",
    status: "Approved",
    createdAt: now,
    updatedAt: now,
    applicantName: "Omar Benali",
    referenceNumber: "CIV-2026-1049",
    documents: [],
    timeline: [
      {
        id: "log-2",
        caseId: "db02aa10-6fd2-4ef6-95cc-5204731858ce",
        action: "approved",
        actorId: "admin-user",
        timestamp: now
      }
    ]
  }
];

export const messages: ChatMessage[] = [
  {
    id: "msg-1",
    caseId: "7f4b6c9d-7a65-4b18-b551-e94db6c49a01",
    sender: "assistant",
    body: "Welcome. I can help you prepare the documents for this service.",
    createdAt: now
  },
  {
    id: "msg-2",
    caseId: "7f4b6c9d-7a65-4b18-b551-e94db6c49a01",
    sender: "citizen",
    body: "I want to start a business licence request.",
    createdAt: now
  }
];
