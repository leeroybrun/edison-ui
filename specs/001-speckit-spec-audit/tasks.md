# Tasks: Edison UI Speckit Audit & Consolidation

**Input**: Design documents from `/specs/001-speckit-spec-audit/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested; include acceptance verification within story phases.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Align plan.md with current repo structure and stack references in `specs/001-speckit-spec-audit/plan.md`
- [ ] T002 Validate dev prerequisites and make targets in `README.md` and `Makefile` for backend/frontend startup
- [ ] T003 [P] Document environment variables and defaults for scan roots/watchers in `backend/README.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Define actor identity helper (OS user + display name) and audit entry shape in `backend/src/models/audit.py`
- [ ] T005 Wire audit writer with filesystem confinement and redaction in `backend/src/services/audit_service.py`
- [ ] T006 [P] Establish Edison project discovery configuration (scan roots, ignores, pin storage) in `backend/src/config/settings.py`
- [ ] T007 [P] Create shared error and guard response shapes for UI consumption in `backend/src/api/schemas/common.py`
- [ ] T008 Implement frontend data fetching clients with error/loading/stale handling in `frontend/src/services/apiClient.ts`
- [ ] T009 [P] Add global layout loading/error/focus states for accessibility in `frontend/src/app/layout.tsx`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Consolidated Edison project visibility (Priority: P1) 🎯 MVP

**Goal**: Surface all local Edison projects with health, tasks/sessions/QA counts, and detail pages.

**Independent Test**: With two sample projects, dashboard lists both with counts; opening a project shows tasks/sessions/QA/agents/validators with clear loading/error/empty states.

### Implementation for User Story 1

- [ ] T010 [P] [US1] Implement project discovery endpoint per contract in `backend/src/api/routes/projects.py`
- [ ] T011 [US1] Add project detail aggregation (health, counts, recent activity) in `backend/src/services/project_service.py`
- [ ] T012 [P] [US1] Render projects dashboard with counts and pins in `frontend/src/app/page.tsx`
- [ ] T013 [US1] Build project detail views (tasks/sessions/QA/agents/validators tabs) in `frontend/src/app/projects/[projectId]/page.tsx`
- [ ] T014 [US1] Add empty/error/loading state components for lists in `frontend/src/components/state/`

**Checkpoint**: User Story 1 independently testable

---

## Phase 4: User Story 2 - Guarded updates to Edison work (Priority: P1)

**Goal**: Enable guarded creates/edits/transitions for tasks and sessions with previews, guard messaging, and audit entries.

**Independent Test**: From UI, create a task and transition a session with preview/confirmation; invalid transition blocked with guard reason; audit entries recorded.

### Implementation for User Story 2

- [ ] T015 [P] [US2] Implement session create/transition endpoints with guard previews in `backend/src/api/routes/sessions.py`
- [ ] T016 [P] [US2] Implement task create/edit/transition endpoints with guard previews in `backend/src/api/routes/tasks.py`
- [ ] T017 [US2] Integrate audit entry creation on all guarded writes in `backend/src/services/audit_service.py`
- [ ] T018 [US2] Add UI forms with preview/confirm flows for tasks/sessions in `frontend/src/app/projects/[projectId]/actions.tsx`
- [ ] T019 [US2] Surface guard failure reasons and success audit summaries in `frontend/src/components/alerts/GuardResult.tsx`

**Checkpoint**: User Story 2 independently testable

---

## Phase 5: User Story 3 - Timely awareness of changes (Priority: P2)

**Goal**: Keep data fresh via watchers when available; fall back to polling/manual refresh with visible staleness indicators.

**Independent Test**: External file change updates UI within freshness windows; when watchers disabled, manual refresh/polling resolves staleness indicator.

### Implementation for User Story 3

- [ ] T020 [P] [US3] Implement filesystem watcher event normalization and publish hook in `backend/src/services/watch_service.py`
- [ ] T021 [US3] Provide polling/manual refresh endpoints and freshness timestamps in `backend/src/api/routes/events.py`
- [ ] T022 [P] [US3] Add realtime subscriptions and fallback polling logic in `frontend/src/hooks/useRealtimeUpdates.ts`
- [ ] T023 [US3] Display last-updated and staleness indicators on lists/detail views in `frontend/src/components/status/FreshnessBadge.tsx`

**Checkpoint**: User Story 3 independently testable

---

## Phase 6: User Story 4 - Search, navigation, and pack/config awareness (Priority: P3)

**Goal**: Enable cross-project search/filter navigation and pack/config visibility with bounded edits.

**Independent Test**: Search finds tasks/sessions across projects quickly; pack/config pages load; allowed config edit applies with rollback; unsupported edits blocked.

### Implementation for User Story 4

- [ ] T024 [P] [US4] Implement search endpoints for tasks/sessions/projects with filters in `backend/src/api/routes/search.py`
- [ ] T025 [US4] Add pack/config read surfaces with allowlisted edit preview/apply in `backend/src/api/routes/config.py`
- [ ] T026 [P] [US4] Build frontend search bar and results navigation in `frontend/src/components/search/SearchBar.tsx`
- [ ] T027 [US4] Render pack/config views with preview/rollback UI in `frontend/src/app/projects/[projectId]/config/page.tsx`

**Checkpoint**: User Story 4 independently testable

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T028 [P] Harden error taxonomy and redaction rules across APIs in `backend/src/api/middleware/error_handler.py`
- [ ] T029 [P] Add performance instrumentation and logging for discovery/list endpoints in `backend/src/metrics/observability.py`
- [ ] T030 Refine accessibility (keyboard focus, ARIA) across UI shells in `frontend/src/components/layout/`
- [ ] T031 [P] Update documentation to reflect new flows in `specs/001-speckit-spec-audit/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3–6)**: Depend on Foundational; US1 and US2 are both P1 and should start first (US1 establishes visibility, US2 adds guarded writes), followed by US3 (freshness) then US4 (search/config)
- **Polish (Phase 7)**: Depends on completion of targeted user stories

### User Story Dependencies

- **User Story 1 (P1)**: Independent once foundation is ready
- **User Story 2 (P1)**: Independent once foundation is ready; may read data from US1 but should not be blocked by it
- **User Story 3 (P2)**: Depends on foundational data access; can run in parallel after US1/US2 start
- **User Story 4 (P3)**: Depends on foundational search/config scaffolding; can proceed after US1 visibility endpoints exist

### Parallel Opportunities

- Setup tasks T002–T003 can run in parallel.
- Foundation tasks T006–T009 can run in parallel after T004/T005 begin.
- Per-story: models/services/endpoints and UI tasks marked [P] can proceed concurrently when they touch different files.
- Different user stories can be staffed in parallel after Foundation: e.g., US1 frontend (T012) and US2 backend (T015/T016) can proceed together.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Verify dashboard and project detail visibility per acceptance criteria

### Incremental Delivery

1. Setup + Foundational → ready
2. Add US1 (visibility) → validate
3. Add US2 (guarded writes) → validate
4. Add US3 (freshness) → validate
5. Add US4 (search/config) → validate

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Parallel streams:
   - Stream A: US1 backend/frontend (T010–T014)
   - Stream B: US2 backend/frontend (T015–T019)
   - Stream C: US3 realtime/polling (T020–T023)
   - Stream D: US4 search/config (T024–T027)
3. Reconvene for Polish tasks (T028–T031)
