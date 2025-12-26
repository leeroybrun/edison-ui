# API Contracts — Edison UI Speckit Audit & Consolidation

Format: JSON over HTTP; base path `/api/v1`.

Notes:
- Filesystem state is source-of-truth; APIs must not “invent” state.
- Mutations are explicit and guarded (preview → confirm/apply). No generic “run command” endpoints.
- Remote access is opt-in; when network-exposed, authentication is required (pairing).

## Projects

- `GET /projects` — list projects with health counts; supports filters (pinned, search), pagination.
- `GET /projects/{projectId}` — project detail summary including counts and recent activity.
- `POST /projects/pin` — body: `{ projectPath, pinned }`; pins/unpins a project; guarded to configured roots; records audit entry.

## Sessions

- `GET /projects/{projectId}/sessions` — list sessions; filters: state, search; pagination; supports `view=list|board`.
- `GET /projects/{projectId}/sessions/{sessionId}` — session detail including history, linked tasks, and latest “next/context” outputs when available.
- `GET /projects/{projectId}/sessions/{sessionId}/tasks` — list tasks scoped to a session (same shape/filters as the project tasks endpoint).
- `GET /projects/{projectId}/sessions/{sessionId}/next` — latest “session next” output (text + timestamp) when available.
- `GET /projects/{projectId}/sessions/{sessionId}/context` — latest “session context” output (text + timestamp) when available.

Mutations (guarded):
- `POST /projects/{projectId}/sessions` — create session; supports preview/confirm; audit entry on success.
- `POST /projects/{projectId}/sessions/{sessionId}/transition` — guarded transition; supports preview/confirm; audit entry on success.

## Tasks

- `GET /projects/{projectId}/tasks` — list tasks across the project, including tasks not associated with any session.
  - Filters: `sessionId` (including a “none” value), `state`, `tags`, `search`, `validatedState`, `owner`
  - Views: `view=list|board|tree`
  - Pagination required for list responses.
- `GET /projects/{projectId}/tasks/{taskId}` — task detail including hierarchy (parent/children), dependencies, and QA linkage.
- `GET /projects/{projectId}/tasks/{taskId}/blockers` — “why blocked” explanation (dependencies + guard readiness) when available.

Mutations (guarded):
- `POST /projects/{projectId}/tasks` — create task; preview/confirm; audit entry on success.
- `PATCH /projects/{projectId}/tasks/{taskId}` — edit task fields; preview/confirm; audit entry on success.
- `POST /projects/{projectId}/tasks/{taskId}/transition` — guarded transition; preview/confirm; audit entry on success.

## QA / Validation (first-class)

- `GET /projects/{projectId}/qa` — list QA rounds across the project; supports filters (taskId, verdict/status, validator, sessionId).
- `GET /projects/{projectId}/tasks/{taskId}/qa` — all QA rounds for a task (including evidence links and validator details).
- `GET /projects/{projectId}/sessions/{sessionId}/qa` — QA rounds scoped to a session (equivalent to filtering the project QA list by `sessionId`).
- `GET /projects/{projectId}/validators` — list known validators (capabilities/metadata).
- `GET /projects/{projectId}/validators/runs` — list recent/active validator runs; filters: taskId, sessionId, status.

Mutations (guarded):
- `POST /projects/{projectId}/tasks/{taskId}/validate` — trigger validation; preview/confirm; audit entry on success.

## Agents (monitoring)

- `GET /projects/{projectId}/agents` — list known agents (capabilities/metadata).
- `GET /projects/{projectId}/agents/runs` — list recent/active agent runs; filters: sessionId, taskId, status.
- `GET /projects/{projectId}/sessions/{sessionId}/agents/runs` — agent runs scoped to a session (equivalent to filtering project agent runs by `sessionId`).
- `GET /projects/{projectId}/sessions/{sessionId}/validators/runs` — validator runs scoped to a session (equivalent to filtering project validator runs by `sessionId`).

## Search

- `GET /search` — global search across pinned/all discovered projects; supports `scope=projects|tasks|sessions|qa|memory` and filters; returns typed hits.
- `GET /projects/{projectId}/search` — project-scoped search with the same shapes.

## Activity / Audit Logs

These endpoints surface Edison core logs (append-only JSONL) and session activity logs for UI observability.

- `GET /projects/{projectId}/activity` — unified activity stream (project-scoped) with filters:
  - `sessionId?`, `taskId?`, `scope=high_level|audit`, `eventPrefix?` (e.g., `cli.`, `subprocess.`, `orchestrator.`, `guard.`, `hook.`), `since?`, pagination.
- `GET /projects/{projectId}/sessions/{sessionId}/activity` — session-scoped unified activity stream (equivalent to filtering project activity by `sessionId`).
- `GET /projects/{projectId}/tasks/{taskId}/activity` — task-scoped unified activity stream (joins task/session metadata with audit events when available).
- `GET /projects/{projectId}/invocations` — list invocation summaries (invocation_id, command, ts, duration, exit_code) with filters (sessionId, since).
- `GET /projects/{projectId}/invocations/{invocationId}` — invocation detail including references to captured stdout/stderr/python logs when available.

## Settings / Runtime

- `GET /settings` — read UI/server settings (scan roots, pins, exposure mode, redaction policy summary).
- `PATCH /settings` — update allowlisted settings with preview/confirm and audit entry where applicable.

## Remote Access Pairing (opt-in)

Applies only when the server is network-exposed (not localhost-only).

- `POST /pairing/start` — begins pairing; returns a short-lived code/QR payload and expiration.
- `POST /pairing/complete` — exchanges a valid pairing code for an auth token.
- `POST /auth/logout` — revoke current token (local device).
- All non-public endpoints MUST require auth when remote mode is enabled.

## Realtime (push-first subscriptions)

### Transport

- `WS /api/v1/realtime`

### Frames (request/reply + push events)

All frames are JSON objects with:
- `id`: client-chosen correlation id
- `type`: message type
- `ok`: boolean (replies/events)
- `payload`: typed payload
- `error`: `{ code, message, details? }` (for `ok=false`)

### Subscribe / Unsubscribe

- `subscribe` payload: `{ subscriptionId, resource, projectId, params? }`
  - `subscriptionId` is client-chosen and stable across reconnects.
  - `resource` examples: `projects`, `tasks`, `task-detail`, `sessions`, `session-detail`, `qa`, `agent-runs`, `validator-runs`
- `unsubscribe` payload: `{ subscriptionId }`

### Push envelopes

Push events carry a per-subscription `revision` for stale-update protection and MUST be applied in-order per `subscriptionId`:

- `snapshot` payload: `{ subscriptionId, revision, items: [...] }`
- `upsert` payload: `{ subscriptionId, revision, item: {...} }`
- `delete` payload: `{ subscriptionId, revision, id: string }`

### Reconnect behavior

On reconnect, clients resubscribe using the same `subscriptionId` values. Server responds with a fresh `snapshot` and restarts `revision` at 1 for that subscription.
