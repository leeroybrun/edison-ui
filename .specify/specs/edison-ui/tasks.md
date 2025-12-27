# Edison UI - Task Breakdown (v0.1 → v1.0)

**Status**: Draft (importable, milestone-based)  
**Last updated**: 2025-12-20

This single task list contains the full path to a fully featured v1.0, organized into milestones so you can deliver incrementally without losing the end-state vision.

## Import
```bash
edison task import .specify/specs/edison-ui/tasks.md
```

## Milestone v0.1 — Read-only MVP (discover + browse)

### TASK-001: Backend FastAPI skeleton + health
- Backend app + `/api/v1/health`.
- CORS middleware, error handler, logging setup.
- Pydantic settings for env config.
- Tests: health endpoint returns 200 + version info.

### TASK-002: Frontend Next.js skeleton + nav shell
- Next.js 14 App Router + TypeScript + Tailwind.
- App layout + "Projects" route placeholder.
- Zustand store setup, TanStack Query provider.
- Tests: header/nav renders, mobile responsive.

### TASK-003: Project discovery service (filesystem)
- Scanner: configured roots, max depth, ignore dirs, permission-safe.
- Stable `projectId` derived from absolute path hash (hashlib.sha256).
- Handle permission errors gracefully, skip inaccessible dirs.
- Cache discovery results (5 min TTL).
- Tests: discovery correctness + ignore rules + permission handling.

### TASK-004: Projects API (read-only)
- `GET /api/v1/projects`, `GET /api/v1/projects/{projectId}`.
- Tests: list/detail + 404 on unknown id.

### TASK-005: Projects UI (read-only)
- Projects list with search and pinned projects.
- Project overview shell with tabs: Tasks / Sessions / QA / Edison.
- Tests: filter behavior.

### TASK-006: Sessions API (read-only)
- `GET /projects/{projectId}/sessions` and `.../sessions/{sessionId}`.
- Use Edison session APIs with explicit `project_root`.
- Tests: fixture project with empty + populated sessions.

### TASK-007: Tasks API (read-only)
- `GET /projects/{projectId}/tasks` and `.../tasks/{taskId}`.
- Tests: fixture project with at least one task.

### TASK-008: QA API (read-only)
- `GET /projects/{projectId}/qa` and `.../qa/{taskId}`.
- Tests: fixture project with QA/evidence structure.

### TASK-009: Tasks/Sessions/QA UI (read-only)
- Lists + detail views + markdown rendering.
- Tests: empty/loading/error states.

### TASK-010: Edison meta browser (agents/validators) (read-only)
- API parses `.edison/_generated/AVAILABLE_AGENTS.md` and `AVAILABLE_VALIDATORS.md`.
- UI presents filterable lists and detail panels.
- Tests: parsing is resilient to missing files.

### TASK-011: Hardening: staleness + refresh/polling + error taxonomy
- Per-page refresh control and optional polling interval.
- Standardize backend error shape; consistent UI error states.

### TASK-012: Accessibility + responsive pass
- Keyboard navigation, landmarks, focus, mobile layouts validated for core pages.

## Milestone v0.2 — Safe Writes (tasks + sessions)

### TASK-020: Audit log model (local-first)
- Define a minimal audit entry format (who/what/when/result).
- Persist as append-only file under project (or UI local store) with clear retention policy.

### TASK-021: Write: create session (guarded)
- Backend endpoint to create sessions (Edison API preferred; CLI fallback if required).
- Input validation with Pydantic, sanitize session_id.
- UI flow: form → preview → confirm → result + audit entry.
- Audit log: timestamp, action, old/new state, outcome.
- Tests: creation in fixture repo (or temp repo) and state visible after refresh.
- Tests: duplicate session_id handling, invalid input rejection.

### TASK-022: Write: session transitions (guarded)
- Endpoint to transition session state, respecting Edison guards.
- Return guard results with can_override flags.
- UI: show allowed transitions + guard explanations + confirmation.
- For failed guards: show why and how to resolve.
- Tests: invalid transition returns structured error with guard details.
- Tests: force flag overrides soft guards only.

### TASK-023: Write: create task (guarded)
- Endpoint to create tasks with required fields and optional QA creation.
- UI: quick-create and full-create flows.
- Tests: task appears in correct status list.

### TASK-024: Write: task edit + transitions (guarded)
- Update task title/description/tags where supported; transition status via Edison APIs.
- UI: inline edit + “Move” actions with confirmation.
- Tests: transition rules respected.

### TASK-025: Bulk operations (bounded)
- Multi-select move (small batches), with preview and rollback guidance.
- Tests: batch failure reports partial results clearly.

## Milestone v0.3 — Realtime (watchers + push)

### TASK-030: File watcher + event normalization
- Watch `.project/` and relevant `.edison/_generated/` outputs using Watchdog.
- Debounce rapid changes (100ms window).
- Normalize file events → domain events (task updated, session updated, QA round added).
- Parse Edison file paths to extract entity type and ID.
- Tests: simulated file writes produce expected events.
- Tests: handles file move/rename correctly.

### TASK-031: Realtime transport
- WebSocket endpoint with per-project subscriptions (socket.io or native WS).
- Message protocol: subscribe/unsubscribe/ping + entity updates.
- Client hook: reconnect, exponential backoff (1s, 2s, 4s...), fallback to polling.
- Connection manager: track subscriptions, broadcast to channels.
- Tests: connect/sub/unsub and event delivery.
- Tests: handles reconnection without duplicate events.

### TASK-032: UI reconciliation rules
- Filesystem is truth; reconcile updates without UI-only state drift.
- Surface “external change” indicators for concurrent CLI actions.

### TASK-033: Notifications (opt-in)
- In-app notifications for important events; optional desktop notifications.
- Tests: notification generation and dismissal.

## Milestone v0.4 — Packs / Config (safe browsing → safe editing)

### TASK-040: Config browsing
- Read-only browse for `.edison/config/*` and generated state machine docs.
- UI: diff viewer and search within config.

### TASK-041: Schema-backed config validation (read-only)
- Load Edison schemas; validate configs and show errors without modifying files.
- Tests: invalid config fixtures show actionable diagnostics.

### TASK-042: Safe config edits (bounded)
- Edit a small allowlist of fields (e.g. scan roots, polling interval) with backup + rollback.
- Tests: rollback restores prior state.

### TASK-043: Pack manager surface
- View enabled packs and what they provide (agents/validators/guidelines).
- Enable/disable packs only if Edison supports it safely; otherwise show CLI instructions.

## Milestone v0.5 — Search, Navigation, Power UX

### TASK-050: Global search (IDs + text)
- Index tasks/sessions/QA metadata and provide fast search.
- Tests: query correctness and result ranking basics.

### TASK-051: Saved filters + views
- Persist user preferences (local browser storage first; optional backend later).
- Tests: filters persist and restore.

### TASK-052: Command palette
- Navigation + safe actions (bounded to allowlisted operations).
- Tests: palette routes correctly and respects permissions.

## Milestone v0.6 — Git Integration (bounded)

### TASK-060: Git read integration for sessions
- Show branch, status, and recent commits for a session worktree.
- Tests: fixture repo shows expected values.

### TASK-061: Commit helper (safe write)
- Commit flow with task-aware template, explicit diff preview, and confirmation.
- Tests: commit created and linked to task metadata (where feasible).

## Milestone v0.7 — QA/Validation Controls (bounded)

### TASK-070: Trigger validation runs (safe)
- Backend endpoint to trigger Edison validations for a task/session (allowlisted).
- UI: run, show progress, capture outputs, link evidence.
- Tests: dry-run mode and error handling.

### TASK-071: Validation wave UI
- Show wave-by-wave progress and verdict aggregation.
- Tests: rendering with mixed pass/fail.

## Milestone v1.0 — Fully Featured, Polished

### TASK-090: Analytics dashboard (local-first)
- Time-in-state, validation pass rate, bottleneck views, export.

### TASK-091: Mobile-first polish + offline considerations
- Mobile UX review; optional offline read cache (explicitly non-authoritative).

### TASK-092: Packaging / “one-command run”
- Provide a “single command” local run experience; optional desktop wrapper is deferred unless required.

### TASK-093: Security hardening checklist
- Allowlist enforcement, path traversal protections, safe file reads, redaction of secrets in UI.

### TASK-094: Performance pass
- Large-project behavior: pagination, virtualization, background indexing.
