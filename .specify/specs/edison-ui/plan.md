# Edison UI - Technical Implementation Plan (v1 Target)

**Status**: Draft (incremental milestones to v1)  
**Last updated**: 2025-12-20

## Architecture (end state)

- **Backend**: FastAPI (Python) that:
  - discovers Edison projects on disk
  - reads/operates Edison state via Edison public APIs
  - falls back to **allowlisted Edison CLI commands** only where Edison lacks a stable API
  - exposes REST endpoints + realtime channel (WebSocket/SSE) for live updates
- **Frontend**: Next.js (App Router) + TypeScript + Tailwind, optimized for both desktop and mobile.
- **Source of truth**: Edison project filesystem (`.edison/`, `.project/`, worktrees).
- **Local-first**: runs locally; cloud deployment is optional and not required for v1.

## Milestone-driven backend plan

### v0.1 (read-only)
- REST-only read endpoints.
- Explicit refresh + optional polling.

### v0.2 (safe writes)
- Add “write” endpoints for:
  - create session/task/QA where supported
  - transition session/task states via Edison APIs
- Safety gates: confirm/preview, strict validation, audit log.
- If CLI fallback is required, enforce:
  - allowlist of subcommands
  - explicit project root and session/worktree confinement
  - captured stdout/stderr recorded as evidence/audit entries

### v0.3 (realtime)
- File watchers for `.project/` and relevant `.edison/_generated/` artifacts.
- Backend push updates to subscribed clients.
- Client reconciliation rules: filesystem always wins; UI does not attempt to “correct” Edison.

### v0.4–v1.0 (advanced)
- Config browser/editor with schema validation + rollback.
- Agents/validators/packs management surfaces (safe, bounded).
- Analytics aggregation (local-only; opt-in).

## API Surface (stable shape, grows over milestones)

Base:
- `GET /api/v1/health`

Projects:
- `GET /api/v1/projects`
- `GET /api/v1/projects/{projectId}`

Sessions:
- `GET /api/v1/projects/{projectId}/sessions`
- `GET /api/v1/projects/{projectId}/sessions/{sessionId}`
- (v0.2+) `POST /api/v1/projects/{projectId}/sessions`
- (v0.2+) `POST /api/v1/projects/{projectId}/sessions/{sessionId}/transition`

Tasks:
- `GET /api/v1/projects/{projectId}/tasks`
- `GET /api/v1/projects/{projectId}/tasks/{taskId}`
- (v0.2+) `POST /api/v1/projects/{projectId}/tasks`
- (v0.2+) `POST /api/v1/projects/{projectId}/tasks/{taskId}/transition`
- (v0.2+) `PATCH /api/v1/projects/{projectId}/tasks/{taskId}` (edit title/description/tags)

QA / Validation:
- `GET /api/v1/projects/{projectId}/qa`
- `GET /api/v1/projects/{projectId}/qa/{taskId}`
- (v0.2+) `POST /api/v1/projects/{projectId}/qa/{taskId}/validate`

Edison meta:
- `GET /api/v1/projects/{projectId}/edison/agents`
- `GET /api/v1/projects/{projectId}/edison/validators`
- (v0.4+) `GET/PUT /api/v1/projects/{projectId}/edison/config` (bounded)

Realtime (v0.3+):
- `WS /api/v1/realtime` (or SSE if simpler), with per-project subscriptions.

Notes:
- `projectId` is a stable, opaque ID derived from absolute path (hash).
- Pagination should be supported early (`limit/cursor`), even if initial datasets are small.

## Frontend plan

### Routing (grows over time)
- `/` projects dashboard
- `/projects/[projectId]` overview
- `/projects/[projectId]/tasks`
- `/projects/[projectId]/sessions`
- `/projects/[projectId]/qa`
- `/projects/[projectId]/edison` (agents/validators/packs/config)

### UX patterns (v1)
- Consistent entity list → detail layouts (mobile-friendly).
- “Dangerous” operations: preview → confirm → execute → outcome + audit entry.
- Command palette: fast navigation + safe actions.

## Data Modeling

- Mirror Edison’s schemas:
  - Tasks: `todo|wip|blocked|done|validated`
  - Sessions: `draft|active|blocked|done|closing|validated|recovery|archived`
- Use Pydantic response models and Zod boundary validation.

## Testing Strategy

- Backend: pytest + FastAPI TestClient; filesystem fixtures via `tmp_path`.
- Frontend: Vitest + RTL for components; Playwright for core user journeys (v0.2+).
- Realtime: integration tests that simulate file change → backend event → UI reconciliation.
