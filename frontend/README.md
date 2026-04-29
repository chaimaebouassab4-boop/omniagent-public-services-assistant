# Civic Services Frontend

React + TypeScript frontend for the public services case management system.

## Stack

- Vite + React 18
- TypeScript strict mode
- Tailwind CSS
- React Router
- React Hook Form + Zod
- Axios with JWT interceptor

## Routes

- `/` service selection
- `/chat/:serviceId` real-time-ready chat
- `/upload/:caseId` document upload
- `/cases` citizen case tracking
- `/admin/login` admin authentication
- `/admin` protected admin dashboard
- `/admin/case/:id` protected admin case details

## Setup

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

The UI includes local seed fallbacks so it can be reviewed before the backend skeleton is completed.

## Environment

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

## Integration Contract

JWT access tokens are stored in `localStorage` and sent as:

```http
Authorization: Bearer <token>
```

HTTP responses are expected to follow:

```json
{ "data": {}, "status": "success" }
```

Errors are expected to follow:

```json
{ "error": "message", "code": 400 }
```
