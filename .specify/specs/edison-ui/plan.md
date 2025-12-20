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

### Testing Patterns
- **No Edison Mocks**: Always test with real Edison integration using fixtures
- **Coverage Targets**: 80% minimum (critical paths: 100%)
- **Test Organization**:
  - `tests/unit/` - isolated component/function tests
  - `tests/integration/` - API endpoint tests with Edison
  - `tests/e2e/` - full user journey tests
- **Fixture Strategy**: Create minimal Edison projects in temp directories

## Security Implementation

### Authentication (future multi-user)
- JWT tokens with 24h expiration
- Refresh token pattern
- Session-based for initial v0.1-v0.3

### Rate Limiting
- Read endpoints: 100/minute
- Write endpoints: 10/minute
- Per-IP or per-session

### Input Sanitization
```python
# Example Pydantic validator
from pydantic import BaseModel, validator
import bleach

class CreateTaskRequest(BaseModel):
    title: str

    @validator('title')
    def sanitize_title(cls, v):
        return bleach.clean(v, tags=[], strip=True)
```

## Caching Strategy

### Redis Cache (optional for v0.1, recommended for v0.3+)
- **Cache Keys & TTL**:
  - `projects:list:{filters_hash}` - 5 min
  - `sessions:list:{project_id}:{state}` - 1 min
  - `tasks:board:{project_id}` - 1 min
  - `search:results:{query_hash}` - 10 min
  - `config:project:{project_id}` - 30 min

### Cache Invalidation
- On write operations: invalidate related keys
- On file change events: invalidate affected entities
- Manual refresh: clear all project-related cache

## WebSocket Implementation

### Message Protocol
```typescript
// Client → Server
{ type: 'subscribe', channels: ['project:id', 'task:*'], correlationId: 'uuid' }

// Server → Client
{ type: 'entity:update', channel: 'task:123', data: {...}, timestamp: 'ISO8601' }
```

### Connection Management
- Heartbeat/ping every 30s
- Auto-reconnect with exponential backoff
- Queue messages during disconnection

## Docker Configuration

### Development
```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    volumes:
      - ~/.project:/projects:ro  # Read-only Edison projects
      - ./backend:/app
    environment:
      - EDISON_PATH=/edison
    ports: ["8000:8000"]

  frontend:
    build: ./frontend
    volumes:
      - ./frontend:/app
    ports: ["3000:3000"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
```

### Production
- Multi-stage builds for smaller images
- Health checks on all services
- Resource limits defined
- Secrets via environment variables

## CI/CD Pipeline

### GitHub Actions Workflow
1. **On PR**: lint → test → build
2. **On merge to main**: deploy to staging
3. **On tag**: deploy to production

### Quality Gates
- Tests must pass
- Coverage > 80%
- No security vulnerabilities
- Lighthouse score > 90

## Error Codes

### Taxonomy
```python
# Edison errors (1xxx)
EDISON_STATE_INVALID = "1001"
EDISON_GUARD_FAILED = "1002"

# Validation errors (2xxx)
VALIDATION_FAILED = "2001"
REQUIRED_FIELD_MISSING = "2002"

# System errors (5xxx)
INTERNAL_ERROR = "5001"
SERVICE_UNAVAILABLE = "5002"
```
