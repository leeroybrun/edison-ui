# Tasks: Edison UI Speckit Audit & Consolidation

**Input**: Design documents from `/specs/001-speckit-spec-audit/`  
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/  
**Tests**: Not explicitly requested; include acceptance verification within story phases.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 Align `specs/001-speckit-spec-audit/plan.md` with current repo structure and updated story set
- [ ] T002 Validate dev entrypoints support “single command” local start (documented) in `Makefile` and `README.md`
- [ ] T003 [P] Document environment variables and defaults for scan roots, exposure mode, and realtime in `backend/.env.example` and `backend/README.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No user story work should begin until this phase is complete.

- [ ] T004 Define actor identity helper (OS user + display name) and audit entry shape in `backend/models/` (exact file per repo layout)
- [ ] T005 Wire audit writer with filesystem confinement and redaction in `backend/services/` (exact file per repo layout)
- [ ] T006 [P] Establish project discovery configuration (scan roots, ignores, pin storage) in `backend/core/` (settings)
- [ ] T007 [P] Create shared error + guard response shapes for UI consumption in backend API schemas
- [ ] T008 Implement frontend API client with consistent error/loading/stale handling in `frontend/lib/` or `frontend/services/`
- [ ] T009 [P] Add navigation shell (sidebar + top bar), loading/error boundaries, and accessibility focus states in `frontend/app/`

**Checkpoint**: Foundation ready

---

## Phase 3: User Story 1 — Zero-setup project dashboard + navigation shell (P1)

- [ ] T010 [US1] Implement project discovery/list/detail endpoints per `specs/001-speckit-spec-audit/contracts/api.md`
- [ ] T011 [P] [US1] Implement first-run settings flow (scan roots + safe defaults) in backend settings endpoints
- [ ] T012 [P] [US1] Build dashboard UI (projects, health counts, pins, recent activity) in `frontend/app/`
- [ ] T013 [US1] Build project shell with sidebar navigation (Dashboard / Sessions / Tasks / QA / Agents / Settings) in `frontend/app/projects/[projectId]/`

**Checkpoint**: US1 independently testable (read-only)

---

## Phase 4: User Story 2 — Board-first + keyboard-first Tasks & Sessions workspace (P1)

- [ ] T020 [US2] Implement unified tasks listing endpoint: project-wide tasks + session filter + hierarchy fields
- [ ] T021 [US2] Implement sessions listing endpoint supporting list + board views (state-based grouping)
- [ ] T022 [P] [US2] Implement “why blocked”/readiness endpoint (dependencies + guard readiness) and ready/blocked summaries
- [ ] T023 [P] [US2] Build Tasks view supporting `list|board|tree` and filters (including session filter) in `frontend/app/projects/[projectId]/tasks/`
- [ ] T024 [P] [US2] Build Sessions view supporting `list|board` and session selection in `frontend/app/projects/[projectId]/sessions/`
- [ ] T025 [US2] Ensure session tasks view reuses the same Tasks presentation + filter semantics as project Tasks view
- [ ] T026 [US2] Implement keyboard navigation + command palette for core flows (open task, switch view, filter) in `frontend/components/`

**Checkpoint**: US2 independently testable

---

## Phase 5: User Story 3 — QA as a primary pipeline flow (P1)

- [ ] T030 [US3] Implement QA list + task QA detail endpoints (rounds, validators, reasons, evidence)
- [ ] T031 [P] [US3] Add validation status summary onto task list payloads (for badges and filtering)
- [ ] T032 [P] [US3] Build QA view (filters by verdict/status/validator/session) in `frontend/app/projects/[projectId]/qa/`
- [ ] T033 [US3] Build task detail QA panel with rounds timeline, evidence links (redacted), and clear failure reasons in `frontend/app/projects/[projectId]/tasks/[taskId]/`
- [ ] T034 [P] [US3] Add session-scoped QA view in session detail that reuses the same QA list component (equivalent to filtering global QA by `sessionId`)

**Checkpoint**: US3 independently testable

---

## Phase 6: User Story 4 — Safe, guarded actions with previews + audits (P2)

- [ ] T040 [P] [US4] Implement guarded task create/edit/transition endpoints (preview → confirm/apply) + audit writes
- [ ] T041 [P] [US4] Implement guarded session create/transition endpoints (preview → confirm/apply) + audit writes
- [ ] T042 [P] [US4] Implement guarded “trigger validation” endpoint (preview → confirm/apply) + audit writes
- [ ] T043 [US4] Build UI mutation flows with preview/confirm dialogs and guard failure explanations in `frontend/app/projects/[projectId]/`
- [ ] T044 [US4] Add audit log view and per-entity audit panels

**Checkpoint**: US4 independently testable

---

## Phase 7: User Story 5 — Push-first realtime updates + freshness (P2)

- [ ] T050 [US5] Implement realtime WebSocket endpoint with `subscribe/unsubscribe` and push envelopes `snapshot/upsert/delete` with per-subscription revisioning
- [ ] T051 [P] [US5] Implement backend watchers → refresh/diff → push pipeline with coalescing/backpressure controls
- [ ] T052 [P] [US5] Implement frontend per-subscription stores that apply snapshot/upsert/delete in revision order
- [ ] T053 [US5] Implement reconnect + resubscribe behavior, and fallback polling/manual refresh with staleness indicators

**Checkpoint**: US5 independently testable

---

## Phase 8: User Story 6 — Remote mobile access with pairing (P2)

- [ ] T060 [US6] Implement server exposure modes (localhost vs network-exposed) and enforce auth when exposed
- [ ] T061 [P] [US6] Implement pairing endpoints (start/complete) and token issuance/revocation
- [ ] T062 [US6] Implement UI pairing wizard (show warning, code/QR, confirm paired device)
- [ ] T063 [US6] Ensure realtime WS requires auth in remote mode; verify rejection behavior for unpaired clients

**Checkpoint**: US6 independently testable

---

## Phase 9: User Story 7 — Session context + memory + agent monitoring (P3)

- [ ] T070 [P] [US7] Implement session “next” and “context” read endpoints (wired to Edison CLI outputs when available)
- [ ] T071 [US7] Build session detail panel for next/context outputs with timestamps and redaction
- [ ] T072 [P] [US7] Implement Agents view endpoints for active/recent agent/validator runs (if available) and fallback “unknown/unavailable” states
- [ ] T073 [US7] Build Agents view UI (active workers, session/task association, last heartbeat) with `sessionId` filtering
- [ ] T073a [P] [US7] Add session-scoped Agents panel in session detail that reuses the same Agents list component (equivalent to filtering global Agents by `sessionId`)
- [ ] T074 [P] [US7] Implement search endpoints for `projects|tasks|sessions|qa|memory` scopes
- [ ] T075 [US7] Build search UI (global + project-scoped) with typed results and quick navigation
- [ ] T076 [P] [US7] Implement pack/config read endpoints and allowlisted edit preview/apply endpoints
- [ ] T077 [US7] Build pack/config UI (view + allowlisted edits with preview/rollback guidance)
- [ ] T078 [P] [US7] Implement activity/audit endpoints to surface Edison core JSONL audit logs and session activity logs with filtering + pagination
- [ ] T079 [US7] Build Activity UI: project timeline + session/task timelines, with “high-level vs raw audit” toggle and invocation drill-down

**Checkpoint**: US7 independently testable

---

## Phase 10: Polish & Cross-Cutting

- [ ] T080 [P] Harden redaction rules (API + UI) for evidence paths, settings, and logs
- [ ] T081 [P] Performance instrumentation for list/board/qa endpoints (timings and payload sizes)
- [ ] T082 [P] Accessibility pass (keyboard focus, ARIA, skip links) across navigation shell and board views
- [ ] T083 [P] Update `specs/001-speckit-spec-audit/quickstart.md` with the latest “zero setup”, realtime, and remote pairing steps
