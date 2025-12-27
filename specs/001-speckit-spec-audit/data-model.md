# Data Model — Edison UI Speckit Audit & Consolidation

This document defines the UI-facing entities and key fields needed to satisfy the specification.

## Entities

### Project

- **Identity**: `projectId` (stable identifier derived from path)
- **Attributes**: `path`, `name`, `pinned`, `health` (counts for tasks/sessions/qa), `lastActivityAt`, `hasGit`, `errors[]`
- **Constraints**:
  - `path` must resolve within configured scan roots.
  - Redaction rules must prevent leaking sensitive path segments outside configured roots.

### Session

- **Identity**: `sessionId`
- **Attributes**: `state`, `createdAt`, `updatedAt`, `owner?`, `history[]`, `taskIds[]`
- **Derived/UI Fields**:
  - `latestNext?` (text + `updatedAt`)
  - `latestContext?` (text + `updatedAt`)
- **Constraints**:
  - State transitions are governed by Edison guards.
  - Session “next/context” data may be absent; UI must degrade gracefully.

### Task

- **Identity**: `taskId`
- **Attributes**: `title`, `description?`, `state`, `tags[]`, `createdAt`, `updatedAt`, `sessionId?`
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
  - `isReady?` (boolean)
  - `blockedReasons[]` (human-readable explanations)
  - `blockedByTaskIds[]`

### QARound

- **Identity**: `qaRoundId` (task-scoped id)
- **Attributes**: `taskId`, `sessionId?`, `roundNumber`, `status`, `verdict?`, `startedAt?`, `finishedAt?`
- **Validator details**:
  - `validators[]` (names/ids)
  - `reasons[]` (structured or text)
- **Evidence**:
  - `evidence[]` (links/paths) — must be redacted and confined to project roots

### Agent / Validator (catalog)

- **Identity**: `agentId` / `validatorId`
- **Attributes**: `name`, `description?`, `capabilities[]`, `enabled?`
- **Notes**: Catalog entries are read-only in this scope.

### AgentRun / ValidatorRun (monitoring)

- **Identity**: `runId`
- **Attributes**: `kind` (`agent|validator`), `name`, `status` (`starting|running|idle|finished|failed|unknown`), `projectId`, `sessionId?`, `taskId?`
- **Observability**:
  - `startedAt?`, `updatedAt?`, `lastHeartbeatAt?`
  - `summary?` (short status text)
- **Constraints**:
  - Activity data may be unavailable; UI must degrade gracefully.
  - For any session-scoped run, the same run MUST be discoverable from:
    - a global (project) runs listing filtered by `sessionId`, and
    - the session detail view’s runs listing.

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
