# API Contracts — Edison UI Speckit Audit & Consolidation

Format: RESTful JSON over HTTP; base path `/api/v1`.

## Projects
- `GET /projects` — list projects with health counts; supports filters (pinned, search), pagination.
- `GET /projects/{projectId}` — project detail including tasks/sessions/QA counts and recent activity.
- `POST /projects/pin` — body: { projectPath }; pins/unpins a project; guarded to configured roots; records audit entry.

## Sessions
- `GET /projects/{projectId}/sessions` — list sessions; filters: state, search; pagination.
- `GET /projects/{projectId}/sessions/{sessionId}` — session detail including history and task links.
- `POST /projects/{projectId}/sessions` — create session; requires preview/confirmation; audit entry on success.
- `POST /projects/{projectId}/sessions/{sessionId}/transition` — request transition with guard evaluation; returns preview; confirmation applies change with audit entry.

## Tasks
- `GET /projects/{projectId}/tasks` — list tasks; filters: state, tags, search; pagination.
- `GET /projects/{projectId}/tasks/{taskId}` — task detail including QA linkage.
- `POST /projects/{projectId}/tasks` — create task with preview/confirmation; audit entry on success.
- `PATCH /projects/{projectId}/tasks/{taskId}` — edit task fields; preview/confirmation; audit entry on success.
- `POST /projects/{projectId}/tasks/{taskId}/transition` — guarded transition; returns guard results; confirmation applies with audit entry.

## QA / Validation
- `GET /projects/{projectId}/qa` — list QA rounds grouped by task.
- `GET /projects/{projectId}/qa/{taskId}` — detail for a task’s QA rounds with evidence paths.
- `POST /projects/{projectId}/qa/{taskId}/validate` — trigger validation; preview/confirmation; audit entry on success.

## Agents / Validators
- `GET /projects/{projectId}/agents` — list agents from Edison metadata.
- `GET /projects/{projectId}/validators` — list validators from Edison metadata.

## Freshness & Realtime
- `GET /projects/{projectId}/events` (long-poll or SSE) — stream of filesystem-derived updates when watchers unavailable.
- `WS /realtime` — subscribe/unsubscribe to project channels; emits entity updates with timestamps and sources.
