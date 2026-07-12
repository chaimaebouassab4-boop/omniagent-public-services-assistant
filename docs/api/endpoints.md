# API Endpoints

Base URL (local): `http://localhost:8000`

> **Two API surfaces.** The **active** API is the `omni` router
> (`backend/app/api/omni.py`), which serves the `omniagent/` frontend's
> generated client: **raw** (un-enveloped) JSON, **camelCase** fields, and
> **numeric** ids. See `omni.py` and `tests/backend/test_api.py` for the exact
> shapes. The endpoints documented below describe the **legacy** enveloped API
> (`cases.py` / `chat.py`), kept in the codebase but not mounted. `POST
> /api/admin/login` (auth) applies to both.

### Citizen auth (active — used by omniagent login/signup/profile)

Raw JSON. On success, signup/login return `{ "token": "<jwt>", "user": {...} }`;
the frontend stores the token in `localStorage` and attaches it as
`Authorization: Bearer <token>` on every request.

- `POST /api/auth/signup` — body `{ fullName, email, phone?, password }` (password ≥ 6). `409` if email taken.
- `POST /api/auth/login` — body `{ email, password }`. `401` on bad credentials. Works for citizens and admins.
- `GET /api/auth/me` — current user profile (from the Bearer token; falls back to the demo citizen if unauthenticated).
- `PATCH /api/auth/me` — body `{ fullName?, phone? }` to update the profile.

`user` shape: `{ id, email, fullName, phone, isAdmin, cinFileName, personalDocuments }`.

### Profile documents

- `POST /api/users/me/documents/cin` — multipart `file` (**PNG or PDF only**, ≤ 10 MB). Saves under `uploads/profiles/{user_id}/`, replaces any previous CIN. Returns the refreshed user.
- `POST /api/users/me/documents/personal` — multipart `file` (PDF/PNG/JPEG/WebP, ≤ 10 MB). Appends `{ id, name, size, mimeType, uploadedAt }` to `personalDocuments` (server paths are never exposed). Returns the refreshed user.

### Chat documents

- `POST /api/chat/documents` — multipart `file` (PDF/PNG/JPEG/WebP, ≤ 10 MB) + optional `language` field (`fr`/`ar`/`darija`). For PDFs, text is extracted with `pypdf` and stored as hidden context (sender `document_context`, excluded from listings). Adds a visible `[Document] <name>` user message plus an assistant acknowledgement (returned, `201`).

### Standalone chat history (per user)

Every standalone chat message carries the author's `user_id`; history is
**scoped to the authenticated user** (a `session_id` column exists for future
multi-conversation support).

- `GET /api/chat/messages` — only the current user's messages.
- `DELETE /api/chat/messages` — clears the current user's history (including
  hidden document context); returns `{ "deleted": <count> }`. Used by the
  "Nouvelle discussion" button in the chat UI.

---

The legacy responses follow the envelope:

```json
{ "status": "success", "data": { ... } }
```

Errors return FastAPI's standard shape: `{ "detail": "..." }` with an HTTP error code.

## Authentication

Endpoints marked 🔒 accept a Bearer JWT (`Authorization: Bearer <token>`).
Without a token, the API falls back to a local demo citizen account (dev convenience).
Admin endpoints (🛡️) require a JWT whose user has `is_admin = true`.

### POST /api/admin/login

Authenticate an administrator. Default seeded account: `admin@demo.local` / `admin123`
(override with `ADMIN_EMAIL` / `ADMIN_PASSWORD` env vars).

Request:

```json
{ "email": "admin@demo.local", "password": "admin123" }
```

Response:

```json
{
  "status": "success",
  "data": {
    "tokens": { "accessToken": "<jwt>", "tokenType": "bearer" },
    "user": { "id": "…", "email": "admin@demo.local", "isAdmin": true }
  }
}
```

Errors: `401` invalid credentials.

## Services

### GET /api/services

List the 10 available public services (id, multilingual names, icon, average
processing days, required documents).

### GET /api/services/{service_id}

Details for one service. Errors: `404` unknown service.

## Cases

### POST /api/cases 🔒

Create a case. Request: `{ "service_id": "residence_certificate" }`.
Errors: `404` unknown service.

### GET /api/cases 🔒

List the current citizen's cases.

### GET /api/cases/{case_id} 🔒

Case details with document summary. Errors: `404` not found, `403` not the owner.

### POST /api/cases/{case_id}/upload 🔒

Multipart form upload: fields `doc_type` (string) and `file` (binary).
Stores the file under `uploads/{case_id}/` and records metadata with
`validation_status = "pending"`.

### GET /api/cases/{case_id}/audit 🔒

Full audit trail of a case (created / uploaded / chat_message / approved / rejected).

## Chat

### POST /api/chat 🔒

Ask the assistant a question about a service, optionally attached to a case.

Request:

```json
{
  "service_id": "residence",
  "case_id": null,
  "message": "شنو الوثائق المطلوبة لشهادة السكنى؟",
  "language": "darija"
}
```

`service_id` accepts aliases (`residence`, `birth`, `marriage`, …) which are
normalized to canonical ids. If `case_id` is provided, the case's service is
used and the exchange is persisted to the case chat history.

Response:

```json
{
  "status": "success",
  "data": {
    "response": "…",
    "confidence": 0.92,
    "sources": ["residence/residence_certificate.json"],
    "language": "darija",
    "message_id": "standalone",
    "service_id": "residence_certificate"
  }
}
```

Low-confidence answers (< 0.30) return a clarification fallback instead of a guess.

Errors: `400` neither `service_id` nor a valid `case_id` given.

### GET /api/cases/{case_id}/chat 🔒

Chat history for a case.

## Admin

### GET /api/admin/cases 🛡️

All cases across citizens. Errors: `403` non-admin.

### POST /api/admin/approve/{case_id} 🛡️

Set case status to `approved` and log the action.

### POST /api/admin/reject/{case_id} 🛡️

Request: `{ "reason": "missing documents" }`. Sets status to `rejected`
and logs the reason.

## Mock Verifications

### POST /api/verify/cin

Mock CIN check. Request: `{ "value": "AB123456" }` → always valid (MVP mock).

### POST /api/verify/cnss

Mock CNSS check. Request: `{ "value": "123456789" }` → always valid (MVP mock).

## Health

### GET /

API banner message.

### GET /health

Liveness probe → `{ "status": "ok" }`.

### GET /api/chat/ping

Chat namespace liveness probe.
