---
task_id: 001-speckit-spec-audit-T022
title: Task Readiness Endpoint
round: 1
phase: GREEN
status: complete
---

# T022: Task Readiness Endpoint

## Summary

Implemented the task readiness endpoint as specified in api.md contracts.

## Changed Files

- `backend/api/routes/tasks.py` - Added readiness endpoint
- `backend/api/schemas/tasks.py` - Added readiness schemas (TaskReadinessResponse, BlockedByItem, GuardBlock)
- `backend/services/task_reader.py` - Added readiness computation logic
- `backend/tests/test_api_tasks.py` - Added readiness endpoint tests

## Implementation Details

### Endpoint: GET /api/v1/projects/{projectId}/tasks/{taskId}/readiness

Returns task readiness status including:
- `ready`: boolean indicating if task can be started
- `blockedBy`: array of blocking dependencies with reason
- `guardBlocks`: array of guard rule blocks

### Readiness Logic

A task is ready when:
1. All dependencies are in COMPLETED_STATES (done, validated)
2. No guard rules block the task

### TDD Workflow

1. **RED**: Wrote failing tests for readiness endpoint
2. **GREEN**: Implemented schemas and readiness computation
3. **REFACTOR**: Fixed type annotations for mypy compliance

## Automation Outputs

- Type-check: PASS (mypy - no errors)
- Lint: PASS (ruff - no errors)
- Tests: PASS (208 backend tests including readiness tests)
