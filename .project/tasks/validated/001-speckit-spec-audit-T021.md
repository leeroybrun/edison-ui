---
id: 001-speckit-spec-audit-T021
title: Implement sessions listing endpoint
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
# Implement sessions listing endpoint

<!-- EXTENSIBLE: Summary -->
## Summary

**SpecKit Source**: `specs/001-speckit-spec-audit/tasks.md` -> T021
**Feature**: 001-speckit-spec-audit
**Phase**: Phase 4 | **User Story**: US2 | **Parallelizable**: No

## Required Reading
Before implementing this task, read:
- `specs/001-speckit-spec-audit/spec.md` -> User Story US2
- `specs/001-speckit-spec-audit/data-model.md`
- `specs/001-speckit-spec-audit/contracts/api.md`
- `specs/001-speckit-spec-audit/plan.md`

## Original SpecKit Task
> T021 [US2] Implement sessions listing endpoint supporting list + board views (state-based grouping)

<!-- /EXTENSIBLE: Summary -->

<!-- EXTENSIBLE: ProblemStatement -->
## Problem Statement

Implement a REST API endpoint for listing sessions with support for:
- State filtering (wip, done, validated)
- Pagination (limit/offset)
- Security: Prevent directory traversal via state parameter validation

<!-- /EXTENSIBLE: ProblemStatement -->

<!-- EXTENSIBLE: Objectives -->
## Objectives

- [x] Create SessionReaderService for filesystem-based session reading
- [x] Implement GET /api/v1/projects/{projectId}/sessions endpoint
- [x] Add pagination support (limit/offset)
- [x] Add state filtering with validation
- [x] Prevent directory traversal attacks

<!-- /EXTENSIBLE: Objectives -->

<!-- EXTENSIBLE: AcceptanceCriteria -->
## Acceptance Criteria

- [x] Endpoint returns list of sessions with pagination metadata
- [x] Filtering by state works correctly
- [x] Invalid state parameter returns 400 Bad Request
- [x] Directory traversal attempts are blocked
- [x] Proper error messages for invalid requests

<!-- /EXTENSIBLE: AcceptanceCriteria -->

<!-- EXTENSIBLE: TechnicalDesign -->
## Technical Design

Created:
- `backend/services/session_reader.py` - SessionReaderService class
- `backend/api/routes/sessions.py` - REST endpoint
- `backend/api/schemas/session.py` - Pydantic schemas

Key security implementation:
- `SESSION_STATES = ("wip", "done", "validated")` - whitelist
- State parameter validated against whitelist before filesystem access
- Invalid states raise ValueError, converted to 400 HTTPException

<!-- /EXTENSIBLE: TechnicalDesign -->

<!-- EXTENSIBLE: FilesToModify -->
## Files to Create/Modify

```
# Create
backend/services/session_reader.py
backend/api/routes/sessions.py
backend/api/schemas/session.py
backend/tests/test_api_sessions.py

# Modify
backend/api/routes/__init__.py
backend/api/schemas/__init__.py
```

<!-- /EXTENSIBLE: FilesToModify -->

<!-- EXTENSIBLE: TDDEvidence -->
## TDD Evidence

### RED Phase
- Test file: backend/tests/test_api_sessions.py
- Output: Initial failing tests for session listing endpoint

### GREEN Phase
- Output: All 214 backend tests pass

### REFACTOR Phase
- Notes: Added state parameter validation for security per validation feedback

<!-- /EXTENSIBLE: TDDEvidence -->

<!-- EXTENSIBLE: VerificationChecklist -->
## Verification Checklist

- [x] Tests pass locally
- [x] Linting passes
- [x] Type checking passes (mypy)
- [x] Documentation updated
- [x] TDD evidence captured
- [x] Security review completed

<!-- /EXTENSIBLE: VerificationChecklist -->

<!-- EXTENSIBLE: SuccessCriteria -->
## Success Criteria

- API returns sessions with correct structure per api.md contract
- Pagination works correctly
- Security: Invalid state values are rejected
- Security: Path traversal is prevented

<!-- /EXTENSIBLE: SuccessCriteria -->

<!-- EXTENSIBLE: RelatedFiles -->
## Related Files

- backend/services/session_reader.py
- backend/api/routes/sessions.py
- backend/api/schemas/session.py
- specs/001-speckit-spec-audit/contracts/api.md

<!-- /EXTENSIBLE: RelatedFiles -->

<!-- EXTENSIBLE: Notes -->
## Notes

Implementation completed as part of session happy-pid-34702.
Security fix applied: State parameter validation to prevent directory traversal.
Commit: 805f4e6 - fix: Address validation findings

<!-- /EXTENSIBLE: Notes -->
