---
id: 001-speckit-spec-audit-T022
title: Implement readiness endpoint derived from task graph
owner: happy-pid-34702
session_id: happy-pid-34702
claimed_at: '2026-01-02T15:00:00Z'
last_active: '2026-01-02T18:30:00Z'
created_at: '2026-01-02T15:00:00Z'
updated_at: '2026-01-02T18:30:00Z'
tags:
- speckit
- 001-speckit-spec-audit
- user-story-2
---
# Implement readiness endpoint derived from task graph

<!-- EXTENSIBLE: Summary -->
## Summary

**SpecKit Source**: `specs/001-speckit-spec-audit/tasks.md` -> T022
**Feature**: 001-speckit-spec-audit
**Phase**: Phase 4 | **User Story**: US2 | **Parallelizable**: Yes

## Required Reading
Before implementing this task, read:
- `specs/001-speckit-spec-audit/spec.md` -> User Story US2
- `specs/001-speckit-spec-audit/data-model.md`
- `specs/001-speckit-spec-audit/contracts/api.md`
- `specs/001-speckit-spec-audit/plan.md`

## Original SpecKit Task
> T022 [P] [US2] Implement readiness endpoint derived from task graph (dependencies) with structured `blockedBy[]` explanations

<!-- /EXTENSIBLE: Summary -->

<!-- EXTENSIBLE: ProblemStatement -->
## Problem Statement

Implement a REST API endpoint that computes task readiness based on:
- Task dependencies (depends_on frontmatter)
- Task state (ready tasks have all dependencies completed)
- Structured blockedBy explanations

<!-- /EXTENSIBLE: ProblemStatement -->

<!-- EXTENSIBLE: Objectives -->
## Objectives

- [x] Implement GET /api/v1/projects/{projectId}/tasks/readiness endpoint
- [x] Compute readiness from task dependency graph
- [x] Return structured blockedBy array with explanations
- [x] Add pagination support (limit/offset)
- [x] Add state filtering for query

<!-- /EXTENSIBLE: Objectives -->

<!-- EXTENSIBLE: AcceptanceCriteria -->
## Acceptance Criteria

- [x] Endpoint returns task readiness with blockedBy explanations
- [x] Tasks with incomplete dependencies show blocked status
- [x] Tasks with all dependencies completed show ready status
- [x] Pagination works correctly
- [x] Proper error handling for invalid requests

<!-- /EXTENSIBLE: AcceptanceCriteria -->

<!-- EXTENSIBLE: TechnicalDesign -->
## Technical Design

Extended TaskReaderService:
- Added `get_task_readiness()` method
- Computes dependency graph from `depends_on` frontmatter
- Returns `TaskReadiness` with `is_ready`, `blockedBy[]`

Endpoint:
- GET /api/v1/projects/{projectId}/tasks/readiness
- Query params: limit, offset, state
- Returns TaskReadinessListResponse

<!-- /EXTENSIBLE: TechnicalDesign -->

<!-- EXTENSIBLE: FilesToModify -->
## Files to Create/Modify

```
# Modify
backend/services/task_reader.py - add get_task_readiness()
backend/api/routes/tasks.py - add readiness endpoint
backend/api/schemas/task.py - add TaskReadiness schema

# Create
backend/tests/test_api_tasks.py - readiness tests
```

<!-- /EXTENSIBLE: FilesToModify -->

<!-- EXTENSIBLE: TDDEvidence -->
## TDD Evidence

### RED Phase
- Test file: backend/tests/test_api_tasks.py
- Output: Initial failing tests for readiness endpoint

### GREEN Phase
- Output: All 214 backend tests pass

### REFACTOR Phase
- Notes: Improved code organization

<!-- /EXTENSIBLE: TDDEvidence -->

<!-- EXTENSIBLE: VerificationChecklist -->
## Verification Checklist

- [x] Tests pass locally
- [x] Linting passes
- [x] Type checking passes (mypy)
- [x] Documentation updated
- [x] TDD evidence captured

<!-- /EXTENSIBLE: VerificationChecklist -->

<!-- EXTENSIBLE: SuccessCriteria -->
## Success Criteria

- API returns task readiness with correct structure
- Dependency analysis is accurate
- Blocked tasks have explanations

<!-- /EXTENSIBLE: SuccessCriteria -->

<!-- EXTENSIBLE: RelatedFiles -->
## Related Files

- backend/services/task_reader.py
- backend/api/routes/tasks.py
- backend/api/schemas/task.py
- specs/001-speckit-spec-audit/contracts/api.md

<!-- /EXTENSIBLE: RelatedFiles -->

<!-- EXTENSIBLE: Notes -->
## Notes

Implementation completed as part of session happy-pid-34702.
Commit: 805f4e6 - fix: Address validation findings

<!-- /EXTENSIBLE: Notes -->
