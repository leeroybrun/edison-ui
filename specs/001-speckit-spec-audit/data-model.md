# Data Model — Edison UI Speckit Audit & Consolidation

This document defines the UI-facing entities and key fields needed to satisfy the specification.

## Canonical Filesystem Sources (Edison)

Edison UI is **filesystem-first**. The backend MUST treat the following as canonical inputs (paths are configurable in Edison, but these are the defaults):

### Core workflow state (`.project/`)

- **Sessions** (nested JSON layout):
  - `.project/sessions/<session-state>/<session-id>/session.json`
  - Optional session-scoped records:
    - `.project/sessions/<session-state>/<session-id>/tasks/<task-state>/*.md`
    - `.project/sessions/<session-state>/<session-id>/qa/<qa-state>/*.md`
- **Tasks** (Markdown with YAML frontmatter; state derived from directory):
  - `.project/tasks/<task-state>/*.md`
- **QA records** (Markdown with YAML frontmatter; state derived from directory):
  - `.project/qa/<qa-state>/*.md`
- **Validation evidence** (per task, per round):
  - `.project/qa/validation-evidence/<task-id>/round-<n>/`
    - `bundle-summary.md` (configurable)
    - `implementation-report.md` (configurable)
    - `validator-<validator-id>-report.md` (per validator)
    - additional evidence artifacts (command outputs, coverage, etc.)

### Observability (`.project/logs/edison/`)

- **Audit events** (append-only JSONL; sink paths are configurable):
  - `.project/logs/edison/audit-project.jsonl`
  - `.project/logs/edison/audit-session-<session-id>.jsonl`
  - `.project/logs/edison/invocations/<invocation-id>.jsonl`
  - Optional captured stdio / python logs:
    - `.project/logs/edison/invocations/<invocation-id>.stdout.log`
    - `.project/logs/edison/invocations/<invocation-id>.stderr.log`
    - `.project/logs/edison/invocations/<invocation-id>.python.log`
- **Process events** (append-only JSONL; source of truth for “tracked processes”):
  - `.project/logs/edison/process-events.jsonl`

### Current session scoping (worktree mode)

- `.project/.session-id` (present only when in a session worktree; used for resume/recovery)

## Entities

### Project

- **Identity**: `projectId` (stable identifier derived from path)
- **Attributes**: `path`, `name`, `pinned`, `health` (counts for tasks/sessions/qa), `lastActivityAt`, `hasGit`, `errors[]`
- **Constraints**:
  - `path` must resolve within configured scan roots.
  - Redaction rules must prevent leaking sensitive path segments outside configured roots.

### Session

- **Identity**: `sessionId`
- **Canonical file**: `session.json` stored under `.project/sessions/<state>/<sessionId>/session.json`
- **Attributes (canonical shape)**:
  - `id`, `state`, `phase`
  - `meta`:
    - `sessionId`, `owner?`, `createdAt`, `lastActive`, `status`
    - plus **meta extra** fields (e.g., `autoStarted`, `orchestratorProfile`, etc.)
  - `git`: `worktreePath?`, `branchName?`, `baseBranch`
  - `activityLog[]` (timestamp/message objects)
  - `stateHistory[]`
  - optional `tasks{}` index (UX optimization; NOT source of truth)
- **Derived/UI Fields (computed, not persisted)**:
  - `sessionContext` (structured payload; deterministic)
  - `sessionNext` (recommended actions; computed on demand)
- **Constraints**:
  - State transitions are governed by Edison guards.
  - Session “next/context” are computed outputs; UI must degrade gracefully if Edison is unavailable or config disables fields.

### SessionContextPayload (computed)

Structured, deterministic payload returned by the Edison “session context” command/library:

- **Identity**: `{projectRoot, sessionId?}` (not persisted)
- **Core fields (always present)**:
  - `isEdisonProject` (boolean), `projectRoot` (string), `sessionId?` (string|null)
- **Optional fields (config-driven)**:
  - `sessionState?`, `worktreePath?`, `currentTaskId?`, `currentTaskState?`, `activePacks[]`
  - `constitutions?` paths map (`agents`, `orchestrator`, `validators`)

### Task

- **Identity**: `taskId`
- **Canonical file**: Markdown with YAML frontmatter; state is derived from directory location.
  - Global task: `.project/tasks/<state>/<taskId>.md`
  - Session-scoped task (optional): `.project/sessions/<sessionState>/<sessionId>/tasks/<state>/<taskId>.md`
- **Frontmatter fields (canonical)**:
  - `id`, `title`, `type`, `owner?`, `session_id?`
  - graph fields: `parent_id?`, `child_ids[]`, `depends_on[]`, `blocks_tasks[]`
  - timestamps: `created_at`, `updated_at`, `claimed_at?`, `last_active?`
  - orchestration: `continuation_id?`, `delegated_to?`, `delegated_in_session?`
  - optional: `tags[]`, `priority?`, `estimated_hours?`, `model?`
- **UI Fields**:
  - `state` (semantic state string)
  - `sessionId?` (from `session_id`)
- **Hierarchy**:
  - `parentId?`
  - `childIds[]`
- **Dependencies**:
  - `dependsOn[]` (task ids this task depends on)
  - `blocksTasks[]` (task ids blocked by this task)
- **Validation summary**:
  - `validationStatus` (e.g., `needs_validation|in_progress|rejected|validated|unknown`)
  - `latestQARoundId?`
  - `latestVerdict?`
- **Readiness summary** (when available):
  - `ready` (boolean)
  - `blockedBy[]` (structured list of unmet dependencies)
    - `dependencyId`, `dependencyState?`, `requiredStates[]`, `reason`
  - Compatibility alias (optional): `unmetDependencies[]` (same information with a more explicit shape)

### QARecord (QA file; workflow state)

- **Identity**: `qaId` (filename stem)
- **Canonical file**: Markdown with YAML frontmatter; state derived from directory location.
  - Global: `.project/qa/<state>/<qaId>.md`
  - Session-scoped (optional): `.project/sessions/<sessionState>/<sessionId>/qa/<state>/<qaId>.md`
- **Frontmatter fields (canonical)**:
  - `id`, `task_id`, `title`, `round` (current), `session_id?`
  - `validator_owner?`, `validators[]`, `evidence[]`
  - `created_at`, `updated_at`, `state_history[]`
- **Notes**:
  - The QA file tracks workflow state and links to evidence; detailed per-round evidence is stored under `validation-evidence/`.

### EvidenceRound (validation evidence; per task + round)

- **Identity**: `{taskId, roundNumber}`
- **Canonical directory**: `.project/qa/validation-evidence/<taskId>/round-<n>/`
- **Key artifacts** (filenames are configurable in Edison):
  - `bundleSummary` (structured markdown, typically `bundle-summary.md`)
  - `implementationReport` (structured markdown, typically `implementation-report.md`)
  - `validatorReports[]` (structured markdown, `validator-<id>-report.md`)
- **Tracking hooks (observability)**:
  - `implementationReport.tracking` and `validatorReport.tracking` include live run metadata.

### Agent / Validator (catalog; definitions)

- **Identity**: `agentId` / `validatorId`
- **Attributes**: `name`, `description?`, `capabilities[]`, `enabled?`
- **Notes**:
  - Catalog entries are composed artifacts (from layered config) and are read-only in this scope.
  - “Active agents/validators” in the UI SHOULD be driven by tracking/process data (below), not by catalog entries.

### TrackingRun (monitoring; computed)

- **Identity**: `runId`
- **Primary sources**:
  - Evidence tracking payloads in `implementation-report.md` and `validator-*-report.md`
  - Process index computed from `process-events.jsonl` (for liveness/staleness)
- **Attributes**:
  - `type`: `implementation|validation|orchestrator`
  - `taskId?`, `sessionId?`, `validatorId?`, `round?`, `model?`
  - `processId?`, `hostname?`, `startedAt?`, `lastActive?`, `completedAt?`, `continuationId?`
  - `isRunning?` (best-effort), `isStale?` (config-driven), `state` (`active|stopped`), `processEvent` (latest event)
- **Observability**:
  - `startedAt?`, `updatedAt?`, `lastHeartbeatAt?`
  - `summary?` (short status text)
- **Constraints**:
  - Activity data may be unavailable; UI must degrade gracefully.
  - For any session-scoped run, the same run MUST be discoverable from both:
    - a global (project) runs listing filtered by `sessionId`, and
    - the session detail view’s runs listing.

### ProcessEvent (append-only; from Edison tracking)

- **Identity**: `{runId, ts, event}` (sufficiently unique for UI paging)
- **Canonical file**: `.project/logs/edison/process-events.jsonl`
- **Core fields**:
  - `ts`, `event`, `runId`, `pid`, `hostname`
- **Common indexed fields** (when present):
  - `kind`, `taskId`, `round`, `validatorId`, `sessionId`, `model`
  - `processId`, `processHostname`
  - `startedAt`, `lastActive`, `completedAt`, `stoppedAt`, `stopReason`
  - launcher metadata: `launcherKind`, `launcherPid`, `parentPid`
  - delegation metadata: `agentRole`, `zenRole`, `continuationId`

### AuditEntry

- **Identity**: `actionId` (unique per action) or `timestamp + actionId`
- **Attributes**: `actor` (OS user + display name), `timestamp`, `actionType`, `target` (entity type + id), `outcome`, `context`
- **Constraints**: No secrets; redact sensitive path data.

### AuditEvent (Edison core JSONL)

- **Identity**: `{invocation_id}:{ts}:{event}` (sufficiently unique for UI paging)
- **Attributes**:
  - `ts`, `event`, `pid`, `invocation_id?`, `session_id?`, `project_root`
  - optional fields by event type (examples):
    - `cli.invocation.*`: `command`, `argv`, `exit_code`, `duration_ms`
      - start events may include: `stdout_path`, `stderr_path`, `stdlib_log_path`
    - `subprocess.*`: `argv`, `cwd`, `timeout`, `returncode`, `stdout`/`stderr` (possibly truncated)
    - `orchestrator.launch.*`: `profile`, `pid`, `cwd`, `argv`, prompt metadata (prompt text elided by default)
    - `guard.*`: `domain`, `guard`, `to`, `result`
    - `hook.*`: `hook_id`, `hook_type`, hook-specific fields
- **Constraints**:
  - Redaction must be applied before returning payloads to UI.
  - UI must support “high-level” views that hide noisy/low-signal events by default.

### InvocationArtifact

- **Identity**: `invocation_id`
- **Attributes**: `startedAt`, `endedAt`, `exit_code?`, `duration_ms?`, `stdout_path?`, `stderr_path?`, `python_log_path?`
- **Constraints**:
  - When paths are shown, they must be redacted/confined to project management/log roots.

### PairingSession (remote access)

- **Identity**: `pairingId`
- **Attributes**: `createdAt`, `expiresAt`, `displayCode`, `status` (`pending|completed|expired|revoked`)
- **Security**:
  - `displayCode` is short-lived and one-time-use.
  - Successful pairing yields an auth token scoped to the server instance.

### RealtimeSubscription (push-first updates)

- **Identity**: `subscriptionId` (client-chosen)
- **Attributes**: `resource`, `params`, `lastRevisionApplied`, `lastSnapshotAt`, `lastUpdateAt`
- **Notes**:
  - Events are applied in-order per `subscriptionId` using a monotonic `revision`.
  - Clients ignore stale revisions (`revision <= lastRevisionApplied`).

### SearchHit

- **Identity**: `hitId`
- **Attributes**: `scope` (`project|session|task|qa|memory`), `projectId`, `entityId?`, `title`, `snippet?`, `matchedFields[]`, `source` (e.g., `filesystem|memory-provider-name`)
