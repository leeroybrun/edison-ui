---
task_id: 001-speckit-spec-audit-T020
title: Unified Tasks Listing Endpoint
round: 1
phase: GREEN
status: complete
---

# T020: Unified Tasks Listing Endpoint

## Summary

Implemented the unified tasks listing endpoint as specified in US2 and api.md contracts.

## Changed Files

- `backend/api/routes/tasks.py` - Tasks listing route handler
- `backend/api/schemas/tasks.py` - Pydantic schemas for tasks
- `backend/services/task_reader.py` - Task reader service
- `backend/api/router.py` - Router registration
- `backend/tests/test_api_tasks.py` - Comprehensive test suite

## Implementation Details

### Endpoint: GET /api/v1/projects/{projectId}/tasks

Returns paginated list of tasks for a project with:
- Filter by state, sessionId, parentId
- Pagination (limit/offset)
- Task metadata (title, state, owner, dates, dependencies)

### TDD Workflow

1. **RED**: Wrote failing tests for all endpoint requirements
2. **GREEN**: Implemented schemas, service, and route handler
3. **REFACTOR**: Fixed type annotations for mypy compliance

## Automation Outputs

- Type-check: PASS (mypy - no errors)
- Lint: PASS (ruff - no errors)
- Tests: PASS (208 backend tests)
