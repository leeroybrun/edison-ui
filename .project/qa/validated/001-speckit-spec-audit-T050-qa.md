---
id: 001-speckit-spec-audit-T050-qa
task_id: 001-speckit-spec-audit-T050
title: QA 001-speckit-spec-audit-T050
round: 3
validator_owner: _unassigned_
session_id: happy-pid-42596
created_at: '2025-12-27T13:25:20Z'
updated_at: '2026-01-05T08:20:57Z'
state_history:
- from: waiting
  to: todo
  timestamp: '2026-01-04T18:43:36Z'
  reason: qa.advance_state
- from: todo
  to: wip
  timestamp: '2026-01-05T08:19:47Z'
  reason: cli-qa-promote
- from: wip
  to: done
  timestamp: '2026-01-05T08:19:56Z'
  reason: cli-qa-promote
- from: done
  to: validated
  timestamp: '2026-01-05T08:20:57Z'
  reason: cli-qa-promote
round_history:
- round: 2
  status: reject
  date: '2026-01-04'
  notes: 'global-codex: backend watcher tests failing; websocket contract mismatch;
    lint/build failing'
- round: 3
  status: pending
  date: '2026-01-04'
---
# QA 001-speckit-spec-audit-T050

<!-- EXTENSIBLE: ValidationScope -->
## Validation Scope

**Task:** 001-speckit-spec-audit-T050
**Current Round:** 3 (pending)
**Latest Completed Round:** 2 (rejected)
**Validator(s) Run:** global-codex (CLI) + local command evidence

<!-- /EXTENSIBLE: ValidationScope -->

<!-- EXTENSIBLE: ValidationDimensions -->
## Validation Dimensions

<!-- Validators check these dimensions -->
| Dimension | Status | Score | Notes |
|-----------|--------|-------|-------|
| Architecture | ⏳ Pending | - | |
| Code Quality | ⏳ Pending | - | |
| Testing | ⏳ Pending | - | |
| Documentation | ⏳ Pending | - | |
| Error Handling | ⏳ Pending | - | |
| Performance | ⏳ Pending | - | |
| Security | ⏳ Pending | - | |

<!-- /EXTENSIBLE: ValidationDimensions -->

<!-- EXTENSIBLE: AutomatedChecks -->
## Automated Checks

### Build Status
- [ ] Build passes

### Type Checking
- [ ] Type checking passes

### Linting
- [ ] Linting passes

### Tests
- [ ] All tests pass
- [ ] Coverage meets threshold

<!-- /EXTENSIBLE: AutomatedChecks -->

<!-- EXTENSIBLE: TDDReview -->
## TDD Evidence Review

### RED Phase
- [ ] Failing test created before implementation
- Evidence: 

### GREEN Phase
- [ ] Test passes with minimal implementation
- Evidence: 

### REFACTOR Phase
- [ ] Code refactored without breaking tests
- Evidence: 

<!-- /EXTENSIBLE: TDDReview -->

<!-- EXTENSIBLE: ValidatorVerdicts -->
## Validator Verdicts

<!-- Record verdict from each validator -->

### Round 2 Verdicts (2026-01-04)

| Validator | Verdict | Blocking | Notes |
|-----------|---------|----------|-------|
| global-codex | ❌ reject | ✅ | Failing evidence (`command-*.txt`), backend watcher tests failing even with `WATCHFILES_FORCE_POLLING=1`, and WebSocket contract mismatches (message shapes + missing auth + no push updates). |

<!-- /EXTENSIBLE: ValidatorVerdicts -->

<!-- EXTENSIBLE: Findings -->
## Findings

### Issues Found
- **Backend tests failing**: `backend/tests/test_realtime_watcher.py` fails with `WATCHFILES_FORCE_POLLING=1` (2 failing tests). See `backend-test-realtime-watcher.txt`.
- **Evidence preset failing (custom-minimal)**: `command-type-check.txt`, `command-lint.txt`, `command-test.txt`, `command-build.txt` all exit non-zero.
- **T050 WebSocket contract mismatches**:
  - Message shapes differ from `specs/001-speckit-spec-audit/contracts/api.md` (uses `data/id/code/message` vs `item/itemId/error`).
  - No exposed-mode auth enforcement (`?token=`) on connect.
  - No push `upsert/delete` streaming; only `snapshot` on subscribe.

### Strengths
<!-- List positive aspects -->
- Frontend TypeScript type-check (`npm run type-check`) passed locally. See `frontend-type-check.txt`.

### Recommendations
<!-- List recommendations for improvement -->
- Fix watcher event path handling and/or watchfiles configuration so polling mode reliably emits events in CI/containers.
- Align WebSocket endpoint path/auth/message envelopes/revision semantics with the T050 contract in `specs/001-speckit-spec-audit/contracts/api.md`.
- Fix lint/build configuration issues before re-running validation (Ruff unused imports; Next build ESLint rule resolution).

<!-- /EXTENSIBLE: Findings -->

<!-- EXTENSIBLE: EvidenceLinks -->
## Evidence Links

<!-- Links to validation evidence files -->
- Evidence dir (round-1): `.project/qa/validation-evidence/001-speckit-spec-audit-T050/round-1/`
- Commands: `command-type-check.txt`, `command-lint.txt`, `command-test.txt`, `command-build.txt`
- Extra: `backend-test-realtime-watcher.txt`, `frontend-type-check.txt`
- Validator reports: `validator-global-codex-report.md`, `validator-global-claude-report.md`

<!-- /EXTENSIBLE: EvidenceLinks -->

<!-- EXTENSIBLE: ApprovalStatus -->
## Approval Status

**Approved:** ❌ No
**Approved By:** 
**Approval Date:** 

<!-- /EXTENSIBLE: ApprovalStatus -->

<!-- EXTENSIBLE: FollowUpTasks -->
## Follow-up Tasks

<!-- Tasks created as result of validation -->

<!-- /EXTENSIBLE: FollowUpTasks -->

<!-- EXTENSIBLE: Notes -->
## Notes

<!-- Additional notes from validation -->

<!-- /EXTENSIBLE: Notes -->
