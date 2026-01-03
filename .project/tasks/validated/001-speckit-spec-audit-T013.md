---
id: 001-speckit-spec-audit-T013
title: Build project shell with sidebar navigation in `frontend/app/projects/[projectId]/`
owner: happy-pid-34702
session_id: happy-pid-34702
claimed_at: '2026-01-02T15:00:00Z'
last_active: '2026-01-02T18:30:00Z'
created_at: '2026-01-02T15:00:00Z'
updated_at: '2026-01-02T18:30:00Z'
tags:
- speckit
- 001-speckit-spec-audit
- user-story-1
---
# Build project shell with sidebar navigation in `frontend/app/projects/[projectId]/`

<!-- EXTENSIBLE: Summary -->
## Summary

**SpecKit Source**: `specs/001-speckit-spec-audit/tasks.md` -> T013
**Feature**: 001-speckit-spec-audit
**Phase**: Phase 3 | **User Story**: US1 | **Parallelizable**: No

## Required Reading
Before implementing this task, read:
- `specs/001-speckit-spec-audit/spec.md` -> User Story US1
- `specs/001-speckit-spec-audit/data-model.md`
- `specs/001-speckit-spec-audit/contracts/`
- `specs/001-speckit-spec-audit/plan.md`

## Original SpecKit Task
> T013 [US1] Build project shell with sidebar navigation (Dashboard / Sessions / Tasks / QA / Agents / Settings) in `frontend/app/projects/[projectId]/`

<!-- /EXTENSIBLE: Summary -->

<!-- EXTENSIBLE: ProblemStatement -->
## Problem Statement

Create a project-scoped shell with sidebar navigation providing access to Dashboard, Sessions, Tasks, QA, Agents, and Settings views.

<!-- /EXTENSIBLE: ProblemStatement -->

<!-- EXTENSIBLE: Objectives -->
## Objectives

- [x] Create project layout with sidebar navigation
- [x] Implement navigation links to all project sections
- [x] Add active state highlighting for current route
- [x] Ensure responsive design and accessibility

<!-- /EXTENSIBLE: Objectives -->

<!-- EXTENSIBLE: AcceptanceCriteria -->
## Acceptance Criteria

- [x] Sidebar displays navigation items: Dashboard, Sessions, Tasks, QA, Agents, Settings
- [x] Clicking navigation items routes to correct pages
- [x] Active route is visually highlighted
- [x] Layout is responsive and accessible

<!-- /EXTENSIBLE: AcceptanceCriteria -->

<!-- EXTENSIBLE: TechnicalDesign -->
## Technical Design

Created `frontend/app/projects/[projectId]/layout.tsx` with:
- Server component for async params handling (Next.js 15)
- ProjectSidebar client component for navigation
- Navigation items with icon support
- Active state based on usePathname

<!-- /EXTENSIBLE: TechnicalDesign -->

<!-- EXTENSIBLE: FilesToModify -->
## Files to Create/Modify

```
# Create
frontend/app/projects/[projectId]/layout.tsx
frontend/components/ProjectSidebar.tsx

# Modify
frontend/app/layout.tsx (if needed for nesting)
```

<!-- /EXTENSIBLE: FilesToModify -->

<!-- EXTENSIBLE: TDDEvidence -->
## TDD Evidence

### RED Phase
- Test file: frontend/__tests__/components/ProjectSidebar.test.tsx
- Output: Initial tests for sidebar navigation

### GREEN Phase
- Output: All 99 frontend tests pass

### REFACTOR Phase
- Notes: Cleaned up TODO comment to "Future:" note per validation feedback

<!-- /EXTENSIBLE: TDDEvidence -->

<!-- EXTENSIBLE: VerificationChecklist -->
## Verification Checklist

- [x] Tests pass locally
- [x] Linting passes
- [x] Type checking passes
- [x] Documentation updated
- [x] TDD evidence captured

<!-- /EXTENSIBLE: VerificationChecklist -->

<!-- EXTENSIBLE: SuccessCriteria -->
## Success Criteria

- Users can navigate between project sections via sidebar
- Navigation is keyboard accessible
- Active section is clearly indicated

<!-- /EXTENSIBLE: SuccessCriteria -->

<!-- EXTENSIBLE: RelatedFiles -->
## Related Files

- frontend/app/projects/[projectId]/layout.tsx
- frontend/components/ProjectSidebar.tsx
- frontend/app/projects/[projectId]/page.tsx

<!-- /EXTENSIBLE: RelatedFiles -->

<!-- EXTENSIBLE: Notes -->
## Notes

Implementation completed as part of session happy-pid-34702.
Commit: 805f4e6 - fix: Address validation findings

<!-- /EXTENSIBLE: Notes -->
