# API Contracts — Edison UI

This document defines the HTTP API contracts for Edison UI backend (FastAPI).

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

- **Localhost mode** (default): No authentication required
- **Network-exposed mode**: Bearer token required (obtained via pairing)

```
Authorization: Bearer <pairing-token>
```

---

## Projects

### GET /projects

List all discovered Edison projects.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pinned` | boolean | — | Filter by pinned status |
| `limit` | integer | 100 | Max items (pagination) |
| `offset` | integer | 0 | Pagination offset |

**Response 200:**
```json
{
  "items": [
    {
      "projectId": "string",
      "path": "string (redacted)",
      "name": "string",
      "pinned": true,
      "health": {
        "taskCount": 42,
        "sessionCount": 3,
        "qaCount": 15,
        "activeCount": 2
      },
      "lastActivityAt": "2025-12-27T10:00:00Z",
      "hasGit": true,
      "errors": []
    }
  ],
  "total": 5,
  "limit": 100,
  "offset": 0
}
```

### GET /projects/{projectId}

Get project details.

**Response 200:**
```json
{
  "projectId": "string",
  "path": "string (redacted)",
  "name": "string",
  "pinned": true,
  "health": { ... },
  "lastActivityAt": "2025-12-27T10:00:00Z",
  "hasGit": true,
  "errors": [],
  "config": {
    "scanRoots": ["~/projects"],
    "memoryEnabled": false
  }
}
```

### PATCH /projects/{projectId}/pin

Toggle project pin status.

**Request Body:**
```json
{
  "pinned": true
}
```

**Response 200:**
```json
{
  "projectId": "string",
  "pinned": true
}
```

---

## Tasks

### GET /projects/{projectId}/tasks

List tasks (project-wide, including session-scoped tasks).

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sessionId` | string | — | Filter by session (use `none` for unscoped) |
| `state` | string | — | Filter by state (todo, wip, blocked, done, validated) |
| `validationStatus` | string | — | Filter by validation status |
| `parentId` | string | — | Filter by parent task |
| `search` | string | — | Full-text search |
| `limit` | integer | 100 | Max items |
| `offset` | integer | 0 | Pagination offset |
| `includeHierarchy` | boolean | false | Include parentId/childIds |

**Response 200:**
```json
{
  "items": [
    {
      "taskId": "string",
      "title": "string",
      "state": "wip",
      "sessionId": "string | null",
      "parentId": "string | null",
      "childIds": ["string"],
      "dependsOn": ["string"],
      "blocksTasks": ["string"],
      "validationStatus": "needs_validation",
      "latestVerdict": "rejected | null",
      "ready": true,
      "blockedBy": [],
      "createdAt": "2025-12-27T10:00:00Z",
      "updatedAt": "2025-12-27T10:00:00Z"
    }
  ],
  "total": 42,
  "limit": 100,
  "offset": 0
}
```

### GET /projects/{projectId}/tasks/{taskId}

Get task detail.

**Response 200:**
```json
{
  "taskId": "string",
  "title": "string",
  "body": "string (markdown)",
  "state": "wip",
  "type": "implementation",
  "sessionId": "string | null",
  "owner": "string | null",
  "parentId": "string | null",
  "childIds": ["string"],
  "dependsOn": ["string"],
  "blocksTasks": ["string"],
  "tags": ["string"],
  "priority": "P1",
  "validationStatus": "needs_validation",
  "latestQARoundId": "string | null",
  "latestVerdict": "rejected | null",
  "ready": true,
  "blockedBy": [
    {
      "dependencyId": "T001",
      "dependencyState": "wip",
      "requiredStates": ["done", "validated"],
      "reason": "Dependency T001 is not complete"
    }
  ],
  "createdAt": "2025-12-27T10:00:00Z",
  "updatedAt": "2025-12-27T10:00:00Z",
  "claimedAt": "2025-12-27T10:00:00Z | null"
}
```

### GET /projects/{projectId}/tasks/{taskId}/readiness

Get computed readiness for a task.

**Response 200:**
```json
{
  "taskId": "string",
  "ready": false,
  "blockedBy": [
    {
      "dependencyId": "T001",
      "dependencyState": "wip",
      "requiredStates": ["done", "validated"],
      "reason": "Dependency T001 must be done or validated"
    }
  ],
  "guardBlocks": [
    {
      "guard": "session-active",
      "reason": "Session must be active to work on tasks"
    }
  ]
}
```

### POST /projects/{projectId}/tasks/preview

Preview task creation (dry-run with guard checks).

**Request Body:**
```json
{
  "title": "string",
  "type": "implementation",
  "sessionId": "string | null",
  "parentId": "string | null",
  "dependsOn": ["string"]
}
```

**Response 200:**
```json
{
  "valid": true,
  "guardWarnings": [],
  "preview": { ... }
}
```

**Response 400:**
```json
{
  "valid": false,
  "guardFailures": [
    {
      "guard": "session-active",
      "reason": "Cannot create task: session is not active"
    }
  ]
}
```

### POST /projects/{projectId}/tasks

Create task (after preview confirmation).

**Request Body:**
```json
{
  "title": "string",
  "type": "implementation",
  "sessionId": "string | null",
  "parentId": "string | null",
  "dependsOn": ["string"],
  "confirmed": true
}
```

**Response 201:**
```json
{
  "taskId": "string",
  "auditEntryId": "string"
}
```

### POST /projects/{projectId}/tasks/{taskId}/transition/preview

Preview state transition.

**Request Body:**
```json
{
  "toState": "done"
}
```

**Response 200:**
```json
{
  "valid": true,
  "currentState": "wip",
  "toState": "done",
  "guardWarnings": []
}
```

### POST /projects/{projectId}/tasks/{taskId}/transition

Apply state transition.

**Request Body:**
```json
{
  "toState": "done",
  "confirmed": true
}
```

**Response 200:**
```json
{
  "taskId": "string",
  "previousState": "wip",
  "newState": "done",
  "auditEntryId": "string"
}
```

---

## Sessions

### GET /projects/{projectId}/sessions

List sessions.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `state` | string | — | Filter by state |
| `limit` | integer | 100 | Max items |
| `offset` | integer | 0 | Pagination offset |

**Response 200:**
```json
{
  "items": [
    {
      "sessionId": "string",
      "state": "active",
      "phase": "implementation",
      "owner": "string | null",
      "taskCount": 5,
      "createdAt": "2025-12-27T10:00:00Z",
      "lastActiveAt": "2025-12-27T10:00:00Z",
      "git": {
        "branchName": "feature/foo",
        "baseBranch": "main"
      }
    }
  ],
  "total": 3,
  "limit": 100,
  "offset": 0
}
```

### GET /projects/{projectId}/sessions/{sessionId}

Get session detail.

**Response 200:**
```json
{
  "sessionId": "string",
  "state": "active",
  "phase": "implementation",
  "meta": {
    "owner": "string | null",
    "createdAt": "2025-12-27T10:00:00Z",
    "lastActive": "2025-12-27T10:00:00Z"
  },
  "git": {
    "worktreePath": "string (redacted) | null",
    "branchName": "feature/foo",
    "baseBranch": "main"
  },
  "activityLog": [
    {
      "timestamp": "2025-12-27T10:00:00Z",
      "message": "Session started"
    }
  ],
  "stateHistory": [
    {
      "from": "pending",
      "to": "active",
      "timestamp": "2025-12-27T10:00:00Z"
    }
  ]
}
```

### GET /projects/{projectId}/sessions/{sessionId}/context

Get session context payload (computed).

**Response 200:**
```json
{
  "isEdisonProject": true,
  "projectRoot": "string (redacted)",
  "sessionId": "string",
  "sessionState": "active",
  "worktreePath": "string (redacted) | null",
  "currentTaskId": "string | null",
  "currentTaskState": "wip | null",
  "activePacks": ["python", "typescript"],
  "constitutions": {
    "agents": ".edison/_generated/constitutions/AGENTS.md",
    "orchestrator": ".edison/_generated/constitutions/ORCHESTRATOR.md",
    "validators": ".edison/_generated/constitutions/VALIDATORS.md"
  }
}
```

### GET /projects/{projectId}/sessions/{sessionId}/next

Get session "next" recommendation (computed).

**Response 200:**
```json
{
  "sessionId": "string",
  "recommendation": "string (markdown)",
  "suggestedActions": [
    {
      "action": "claim-task",
      "taskId": "T005",
      "reason": "Task is ready and unassigned"
    }
  ],
  "timestamp": "2025-12-27T10:00:00Z"
}
```

### POST /projects/{projectId}/sessions/{sessionId}/transition/preview

Preview session state transition.

### POST /projects/{projectId}/sessions/{sessionId}/transition

Apply session state transition.

---

## QA

### GET /projects/{projectId}/qa

List QA records.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `taskId` | string | — | Filter by task |
| `sessionId` | string | — | Filter by session |
| `state` | string | — | Filter by QA state |
| `verdict` | string | — | Filter by verdict |
| `limit` | integer | 100 | Max items |
| `offset` | integer | 0 | Pagination offset |

**Response 200:**
```json
{
  "items": [
    {
      "qaId": "string",
      "taskId": "string",
      "sessionId": "string | null",
      "round": 2,
      "state": "done",
      "verdict": "validated",
      "validators": ["code-review", "test-coverage"],
      "createdAt": "2025-12-27T10:00:00Z",
      "updatedAt": "2025-12-27T10:00:00Z"
    }
  ],
  "total": 15,
  "limit": 100,
  "offset": 0
}
```

### GET /projects/{projectId}/qa/{qaId}

Get QA record detail.

**Response 200:**
```json
{
  "qaId": "string",
  "taskId": "string",
  "sessionId": "string | null",
  "round": 2,
  "state": "done",
  "verdict": "validated",
  "validators": ["code-review", "test-coverage"],
  "evidence": [
    {
      "roundNumber": 2,
      "bundleSummary": "string (markdown, redacted)",
      "implementationReport": "string (markdown, redacted) | null",
      "validatorReports": [
        {
          "validatorId": "code-review",
          "verdict": "pass",
          "reason": "string",
          "reportPath": "string (redacted)"
        }
      ],
      "artifacts": [
        {
          "name": "coverage-report.txt",
          "path": "string (redacted)",
          "type": "text/plain"
        }
      ]
    }
  ],
  "stateHistory": [ ... ],
  "createdAt": "2025-12-27T10:00:00Z",
  "updatedAt": "2025-12-27T10:00:00Z"
}
```

### POST /projects/{projectId}/qa/trigger/preview

Preview triggering validation for a task.

### POST /projects/{projectId}/qa/trigger

Trigger validation (after confirmation).

---

## Agents (Tracking)

### GET /projects/{projectId}/agents/active

List currently active agents/validators.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sessionId` | string | — | Filter by session |
| `taskId` | string | — | Filter by task |
| `type` | string | — | Filter by type (implementation, validation, orchestrator) |

**Response 200:**
```json
{
  "items": [
    {
      "runId": "string",
      "type": "validation",
      "taskId": "string | null",
      "sessionId": "string | null",
      "validatorId": "code-review | null",
      "round": 2,
      "model": "claude-3-5-sonnet | null",
      "processId": 12345,
      "hostname": "localhost",
      "startedAt": "2025-12-27T10:00:00Z",
      "lastActiveAt": "2025-12-27T10:05:00Z",
      "isRunning": true,
      "isStale": false,
      "state": "active"
    }
  ],
  "total": 2
}
```

### GET /projects/{projectId}/agents/process-events

Get process events (paginated, append-only stream).

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `since` | string | — | ISO timestamp to start from |
| `runId` | string | — | Filter by run ID |
| `limit` | integer | 100 | Max items |

**Response 200:**
```json
{
  "items": [
    {
      "ts": "2025-12-27T10:00:00Z",
      "event": "started",
      "runId": "string",
      "pid": 12345,
      "hostname": "localhost",
      "kind": "validation",
      "taskId": "string | null",
      "sessionId": "string | null"
    }
  ],
  "hasMore": true
}
```

---

## Activity / Audit

### GET /projects/{projectId}/activity

Get project activity timeline (high-level).

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sessionId` | string | — | Filter by session |
| `taskId` | string | — | Filter by task |
| `eventType` | string | — | Filter by event type |
| `since` | string | — | ISO timestamp |
| `limit` | integer | 50 | Max items |

**Response 200:**
```json
{
  "items": [
    {
      "timestamp": "2025-12-27T10:00:00Z",
      "eventType": "task.transition",
      "summary": "Task T005 moved to done",
      "sessionId": "string | null",
      "taskId": "string | null",
      "invocationId": "string | null",
      "actor": {
        "osUser": "leeroy",
        "displayName": "Leeroy Jenkins"
      }
    }
  ],
  "hasMore": true
}
```

### GET /projects/{projectId}/audit

Get raw audit events (JSONL-backed).

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `invocationId` | string | — | Filter by invocation |
| `sessionId` | string | — | Filter by session |
| `since` | string | — | ISO timestamp |
| `limit` | integer | 100 | Max items |
| `includeRaw` | boolean | false | Include full event payload |

**Response 200:**
```json
{
  "items": [
    {
      "ts": "2025-12-27T10:00:00Z",
      "event": "cli.invocation.end",
      "invocationId": "string",
      "sessionId": "string | null",
      "command": "edison task transition",
      "exitCode": 0,
      "durationMs": 1234
    }
  ],
  "hasMore": true
}
```

---

## Search

### GET /projects/{projectId}/search

Search across entities within a project.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | required | Search query |
| `scope` | string | all | Comma-separated: tasks,sessions,qa,memory |
| `limit` | integer | 20 | Max items per scope |

**Response 200:**
```json
{
  "query": "authentication",
  "results": {
    "tasks": [
      {
        "taskId": "T015",
        "title": "Implement authentication flow",
        "snippet": "...authentication using OAuth2...",
        "score": 0.95
      }
    ],
    "sessions": [],
    "qa": [],
    "memory": [
      {
        "providerId": "file-store",
        "text": "Authentication pattern: use JWT tokens...",
        "score": 0.82,
        "meta": { "source": "patterns.md" }
      }
    ]
  },
  "totalHits": 5
}
```

### GET /search

Global search across all projects.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | required | Search query |
| `projectId` | string | — | Filter to specific project |
| `scope` | string | all | Comma-separated scopes |
| `limit` | integer | 20 | Max items per scope |

---

## Settings

### GET /settings

Get current settings.

**Response 200:**
```json
{
  "scanRoots": ["~/projects", "~/work"],
  "exposureMode": "localhost",
  "realtime": {
    "enabled": true,
    "watcherEnabled": true,
    "pollingIntervalMs": 5000
  },
  "actor": {
    "osUser": "leeroy",
    "displayName": "Leeroy Jenkins | null"
  }
}
```

### PATCH /settings

Update settings (allowlisted fields only).

**Request Body:**
```json
{
  "scanRoots": ["~/projects"],
  "displayName": "Leeroy Jenkins"
}
```

**Response 200:**
```json
{
  "updated": ["scanRoots", "displayName"],
  "auditEntryId": "string"
}
```

### GET /settings/first-run

Check if first-run setup is needed.

**Response 200:**
```json
{
  "needsSetup": true,
  "suggestedRoots": ["~/projects"]
}
```

### POST /settings/first-run

Complete first-run setup.

**Request Body:**
```json
{
  "scanRoots": ["~/projects"],
  "displayName": "Leeroy Jenkins"
}
```

---

## Pairing (Remote Access)

### POST /pairing/start

Start pairing session (requires server in exposed mode).

**Response 200:**
```json
{
  "pairingId": "string",
  "displayCode": "ABC123",
  "expiresAt": "2025-12-27T10:05:00Z",
  "qrCodeDataUrl": "data:image/png;base64,..."
}
```

### POST /pairing/complete

Complete pairing with code.

**Request Body:**
```json
{
  "displayCode": "ABC123"
}
```

**Response 200:**
```json
{
  "token": "string (bearer token)",
  "expiresAt": "2025-12-28T10:00:00Z"
}
```

### DELETE /pairing/{pairingId}

Revoke a pairing session.

---

## Realtime (WebSocket)

### WS /realtime

WebSocket endpoint for push updates.

**Connection:**
- In localhost mode: No auth required
- In exposed mode: Pass `?token=<bearer-token>` query param

**Client → Server Messages:**

```json
{
  "type": "subscribe",
  "subscriptionId": "tasks-list-abc",
  "resource": "tasks",
  "params": {
    "projectId": "string",
    "sessionId": "string | null"
  }
}
```

```json
{
  "type": "unsubscribe",
  "subscriptionId": "tasks-list-abc"
}
```

**Server → Client Messages:**

```json
{
  "type": "snapshot",
  "subscriptionId": "tasks-list-abc",
  "revision": 1,
  "data": [ ... ]
}
```

```json
{
  "type": "upsert",
  "subscriptionId": "tasks-list-abc",
  "revision": 2,
  "item": { ... }
}
```

```json
{
  "type": "delete",
  "subscriptionId": "tasks-list-abc",
  "revision": 3,
  "itemId": "T005"
}
```

```json
{
  "type": "error",
  "subscriptionId": "tasks-list-abc",
  "error": "Resource not found"
}
```

---

## Error Responses

All endpoints use consistent error shapes:

**400 Bad Request:**
```json
{
  "error": "validation_error",
  "message": "Invalid request body",
  "details": [
    { "field": "title", "message": "Required" }
  ]
}
```

**401 Unauthorized (exposed mode only):**
```json
{
  "error": "unauthorized",
  "message": "Valid bearer token required"
}
```

**403 Forbidden:**
```json
{
  "error": "guard_failure",
  "message": "Action blocked by guard",
  "guardFailures": [
    {
      "guard": "session-active",
      "reason": "Session must be active"
    }
  ]
}
```

**404 Not Found:**
```json
{
  "error": "not_found",
  "message": "Task T999 not found"
}
```

**500 Internal Server Error:**
```json
{
  "error": "internal_error",
  "message": "An unexpected error occurred",
  "correlationId": "string"
}
```
