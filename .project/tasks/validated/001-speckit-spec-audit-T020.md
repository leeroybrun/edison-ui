---
id: 001-speckit-spec-audit-T020
title: Implement unified tasks listing endpoint
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
# Implement unified tasks listing endpoint

<!-- EXTENSIBLE: Summary -->
## Summary

**SpecKit Source**: `specs/001-speckit-spec-audit/tasks.md` -> T020
**Feature**: 001-speckit-spec-audit
**Phase**: Phase 4 | **User Story**: US2 | **Parallelizable**: No

## Required Reading
Before implementing this task, read:
- `specs/001-speckit-spec-audit/spec.md` -> User Story US2
- `specs/001-speckit-spec-audit/data-model.md`
- `specs/001-speckit-spec-audit/contracts/api.md`
- `specs/001-speckit-spec-audit/plan.md`

## Original SpecKit Task
> T020 [US2] Implement unified tasks listing endpoint: project-wide tasks + session filter + hierarchy fields

<!-- /EXTENSIBLE: Summary -->

<!-- EXTENSIBLE: ProblemStatement -->
## Problem Statement

Implement a REST API endpoint for listing tasks with support for:
- Project-wide task listing
- Session filtering
- State filtering
- Pagination (limit/offset)
- Hierarchy fields (parent/child relationships)

<!-- /EXTENSIBLE: ProblemStatement -->

<!-- EXTENSIBLE: Objectives -->
## Objectives

- [x] Create TaskReaderService for filesystem-based task reading
- [x] Implement GET /api/v1/projects/{projectId}/tasks endpoint
- [x] Add pagination support (limit/offset)
- [x] Add state and session filtering
- [x] Parse YAML frontmatter including block sequences

<!-- /EXTENSIBLE: Objectives -->

<!-- EXTENSIBLE: AcceptanceCriteria -->
## Acceptance Criteria

- [x] Endpoint returns list of tasks with pagination metadata
- [x] Filtering by state works correctly
- [x] Filtering by session works correctly
- [x] YAML block sequences are parsed correctly
- [x] 400 error returned for invalid parameters

<!-- /EXTENSIBLE: AcceptanceCriteria -->

<!-- EXTENSIBLE: TechnicalDesign -->
## Technical Design

Created:
- `backend/services/task_reader.py` - TaskReaderService class
- `backend/api/routes/tasks.py` - REST endpoint
- `backend/api/schemas/task.py` - Pydantic schemas

Key implementation:
- `_parse_frontmatter()` handles both inline arrays `[a, b]` and block sequences `- item`
- Service scans `.project/tasks/{state}/` directories
- Returns TaskListResponse with items, total, limit, offset

<!-- /EXTENSIBLE: TechnicalDesign -->

<!-- EXTENSIBLE: FilesToModify -->
## Files to Create/Modify

```
# Create
backend/services/task_reader.py
backend/api/routes/tasks.py
backend/api/schemas/task.py
backend/tests/test_api_tasks.py

# Modify
backend/api/routes/__init__.py
backend/api/schemas/__init__.py
```

<!-- /EXTENSIBLE: FilesToModify -->

<!-- EXTENSIBLE: TDDEvidence -->
## TDD Evidence

### RED Phase
- Test file: backend/tests/test_api_tasks.py
- Output: Initial failing tests for task listing endpoint

### GREEN Phase
- Output: All 214 backend tests pass

### REFACTOR Phase
- Notes: Improved YAML parser to handle block sequences per validation feedback

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

- API returns tasks with correct structure per api.md contract
- Pagination works correctly
- Filtering produces expected results

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
