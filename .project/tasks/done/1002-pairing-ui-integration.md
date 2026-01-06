---
id: 1002-pairing-ui-integration
title: Integrate PairingWizard into Settings Page
owner: Leeroy Brun
session_id: happy-pid-66368
relationships:
- type: follows
  target: 001-speckit-spec-audit-T062
claimed_at: '2026-01-05T18:28:27Z'
last_active: '2026-01-05T18:33:33Z'
created_at: '2026-01-05T18:27:09Z'
updated_at: '2026-01-05T18:33:33Z'
tags:
- user-story-6
- frontend
- pairing
---
# Integrate PairingWizard into Settings Page

<!-- EXTENSIBLE: Summary -->
## Summary

The PairingWizard component was implemented in T062 but not integrated into the application routes.
This task adds a Settings page at `/settings` that includes exposure mode toggle and the PairingWizard.

<!-- /EXTENSIBLE: Summary -->

<!-- EXTENSIBLE: ProblemStatement -->
<!-- REQUIRED FILL: ProblemStatement -->
## Problem Statement

The PairingWizard component exists and is fully tested (32 unit tests) but is not accessible
via any route in the application. Users need a way to:
1. Toggle between localhost and network-exposed modes
2. Initiate the pairing flow when in network mode
3. View and manage paired devices

<!-- /EXTENSIBLE: ProblemStatement -->

<!-- EXTENSIBLE: Objectives -->
<!-- REQUIRED FILL: Objectives -->
## Objectives

<!-- List specific, measurable objectives with checkboxes -->
- [x] Create `/settings` route with Settings page
- [x] Add exposure mode toggle (localhost/network)
- [x] Integrate PairingWizard component for network mode pairing
- [x] Add navigation link to Settings in sidebar/header

<!-- /EXTENSIBLE: Objectives -->

<!-- EXTENSIBLE: AcceptanceCriteria -->
<!-- REQUIRED FILL: AcceptanceCriteria -->
## Acceptance Criteria

<!-- List specific criteria that must be met for task completion -->
- [x] Settings page accessible at `/settings`
- [x] Exposure mode toggle works (calls API)
- [x] PairingWizard opens when "Start Pairing" clicked in network mode
- [x] Navigation includes Settings link
- [x] Tests pass for new components
- [x] E2E validation can reach the pairing flow

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
frontend/app/settings/page.tsx
frontend/app/settings/page.test.tsx

# Modify
frontend/components/NavSidebar.tsx (add Settings link)
```

<!-- /EXTENSIBLE: FilesToModify -->

<!-- EXTENSIBLE: TDDEvidence -->
## TDD Evidence

### RED Phase
- Test file: `frontend/app/(main)/settings/page.test.tsx`
- Tests written first, failed with "Failed to resolve import ./page" (page didn't exist)
- NavSidebar test added for Settings link, failed until link was added

### GREEN Phase
- Created `frontend/app/(main)/settings/page.tsx` with exposure mode toggle + PairingWizard
- Added Settings link to `frontend/components/NavSidebar.tsx` and `frontend/app/(main)/layout.tsx`
- All 569 frontend tests pass (12 new tests for Settings page, 1 new for NavSidebar)

### REFACTOR Phase
- No refactoring needed - implementation was clean on first pass

<!-- /EXTENSIBLE: TDDEvidence -->

<!-- EXTENSIBLE: VerificationChecklist -->
## Verification Checklist

- [x] Tests pass locally (569 tests, all passing)
- [x] Linting passes (next lint: no warnings or errors)
- [x] Type checking passes (tsc --noEmit: clean)
- [x] Build passes (next build: success)
- [x] TDD evidence captured
- [x] E2E validation via Playwright MCP (Settings page accessible, exposure toggle works, PairingWizard opens)

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
- frontend/app/(main)/settings/page.tsx
- frontend/app/(main)/settings/page.test.tsx
- frontend/components/NavSidebar.tsx
- frontend/app/(main)/layout.tsx

<!-- /EXTENSIBLE: PrimaryFiles -->

<!-- EXTENSIBLE: Notes -->
## Notes

<!-- Additional notes, context, or considerations -->

<!-- /EXTENSIBLE: Notes -->