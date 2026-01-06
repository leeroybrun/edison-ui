---
id: 1000-wave2-qa-guards-bundle
title: 'Bundle: Wave 2 QA UI + Guarded Task Operations'
session_id: happy-pid-24735
created_at: '2026-01-04T10:14:52Z'
updated_at: '2026-01-04T10:14:52Z'
---
# Bundle: Wave 2 QA UI + Guarded Task Operations

<!-- EXTENSIBLE: Summary -->
## Summary

Session: happy-pid-24735

This bundle groups related QA UI and guarded task operation tasks for consolidated validation:
- T032: QA view with filters (verdict/status/validator/session)
- T033: Task detail QA panel with rounds timeline
- T034: Session-scoped QA view
- T040: Guarded task create/transition endpoints

<!-- /EXTENSIBLE: Summary -->

<!-- EXTENSIBLE: ProblemStatement -->
## Problem Statement

Implement QA-related UI components and guarded task operations to enable:
1. Viewing and filtering QA records across the project
2. Displaying QA details in task panels with validation rounds timeline
3. Session-scoped QA views for focused workflow
4. Safe, guarded task mutations with preview/confirm flow

<!-- /EXTENSIBLE: ProblemStatement -->

<!-- EXTENSIBLE: Objectives -->
## Objectives

- [x] Build QAView component with list/board views and filtering
- [x] Build TaskQAPanel with RoundTimeline for validation evidence
- [x] Add session-scoped QA via lockedSessionId prop
- [x] Implement TaskGuardService for create/transition guards
- [x] Implement TaskWriterService for filesystem operations
- [x] Add guarded API endpoints with preview/confirm pattern

<!-- /EXTENSIBLE: Objectives -->

<!-- EXTENSIBLE: AcceptanceCriteria -->
## Acceptance Criteria

- [x] QAView supports list and board view modes
- [x] QAView filters by state, verdict, session, validator, search
- [x] TaskQAPanel displays QA record with rounds timeline
- [x] RoundTimeline shows evidence artifacts with redacted paths
- [x] Session detail page shows session-scoped QA
- [x] Task guards validate session state, dependencies, transitions
- [x] Preview endpoints return guard results before mutations
- [x] All 337 frontend tests pass
- [x] All 281 backend tests pass

<!-- /EXTENSIBLE: AcceptanceCriteria -->

<!-- EXTENSIBLE: TechnicalDesign -->
## Technical Design

<!-- Optional: Include technical design details, code snippets, diagrams -->

<!-- /EXTENSIBLE: TechnicalDesign -->

<!-- EXTENSIBLE: FilesToModify -->
## Files to Create/Modify

<!-- List files that will be changed -->
```
# Create
path/to/new/file.py

# Modify
path/to/existing/file.py
```

<!-- /EXTENSIBLE: FilesToModify -->

<!-- EXTENSIBLE: TDDEvidence -->
## TDD Evidence

### RED Phase
<!-- Link to failing test output -->
- Test file:
- Output:

### GREEN Phase
<!-- Link to passing test output -->
- Output:

### REFACTOR Phase
<!-- Notes on refactoring performed -->
- Notes:

<!-- /EXTENSIBLE: TDDEvidence -->

<!-- EXTENSIBLE: VerificationChecklist -->
## Verification Checklist

- [ ] Tests pass locally
- [ ] Linting passes
- [ ] Type checking passes
- [ ] Documentation updated
- [ ] TDD evidence captured

<!-- /EXTENSIBLE: VerificationChecklist -->

<!-- EXTENSIBLE: SuccessCriteria -->
## Success Criteria

<!-- Define what success looks like -->

<!-- /EXTENSIBLE: SuccessCriteria -->

<!-- EXTENSIBLE: RelatedFiles -->
## Related Files

<!-- List related files for context -->

<!-- /EXTENSIBLE: RelatedFiles -->

<!-- EXTENSIBLE: PrimaryFiles -->
## Primary Files / Areas

Primary Files / Areas:
- frontend/components/QA/QAView.tsx
- frontend/components/QA/QACard.tsx
- frontend/components/QA/QAFilters.tsx
- frontend/components/QA/RoundTimeline.tsx
- frontend/components/QA/TaskQAPanel.tsx
- backend/services/task_guard.py
- backend/services/task_writer.py
- backend/api/schemas/tasks.py
- backend/api/routes/tasks.py

<!-- /EXTENSIBLE: PrimaryFiles -->

<!-- EXTENSIBLE: Notes -->
## Notes

<!-- Additional notes, context, or considerations -->

<!-- /EXTENSIBLE: Notes -->
