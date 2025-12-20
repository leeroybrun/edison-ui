# Feature Specification: Edison UI Speckit Audit & Consolidation

**Feature Branch**: `001-speckit-spec-audit`  
**Created**: 2025-12-20  
**Status**: Draft  
**Input**: User description: "please analyse ALL the files in this repository, and all the files in /Users/leeroy/Documents/Development/edison-ui/.specify as well, which have been created by claude code manually and then updated by codex. and check if they are correct speckit artifacts/files, otherwise create a real and comprehensive speckit spec from them"

## Clarifications

### Session 2025-12-20

- Q: What actor identity should be recorded for guarded writes and audit entries? → A: Use the local OS user as actor and require an explicit per-session display name for audit logs.

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Consolidated Edison project visibility (Priority: P1)

Developers can open the UI and immediately see every Edison project on the machine with its health, active work (tasks, sessions, QA), and recent activity in one place.

**Why this priority**: This is the primary value of the UI—quick, trustworthy awareness without needing the CLI.

**Independent Test**: Start the UI with multiple sample Edison projects present; confirm users can discover projects, open one, and inspect tasks/sessions/QA details without performing any write actions.

**Acceptance Scenarios**:

1. **Given** configured scan roots include two Edison projects, **When** the user opens the dashboard, **Then** both projects appear with status, last activity, and counts for tasks/sessions/QA.
2. **Given** a project with tasks, sessions, QA rounds, and agent/validator metadata on disk, **When** the user opens that project, **Then** they can view lists and detail pages for each entity with clear loading/error/empty states.

---

### User Story 2 - Guarded updates to Edison work (Priority: P1)

Developers can create or transition tasks and sessions, and trigger validations, with previews, guard explanations, and audit entries so changes are safe and reversible.

**Why this priority**: Teams need to act from the UI, but every write must respect Edison rules and capture who/what/when.

**Independent Test**: In a project fixture, attempt a session transition and a task creation from the UI; verify previews, confirmations, successful writes, and recorded audit entries; verify invalid transitions are blocked with reasons.

**Acceptance Scenarios**:

1. **Given** a draft session, **When** the user requests a transition to active and confirms after reviewing guards, **Then** the session state changes, the UI updates, and an audit entry records actor/time/outcome.
2. **Given** a blocked task, **When** the user attempts an invalid transition, **Then** no file changes occur and the UI shows the guard failure reason and how to resolve it.

---

### User Story 3 - Timely awareness of changes (Priority: P2)

Users are kept aware of changes from CLI activity or background processes via realtime updates when available, with manual refresh/polling fallbacks and clear staleness indicators.

**Why this priority**: Edison state changes outside the UI; users need confidence they are viewing fresh data and can refresh on demand.

**Independent Test**: With filesystem watchers enabled, edit a task via CLI and confirm the UI updates automatically; disable watchers and confirm polling/manual refresh restores freshness with visible timestamp/status cues.

**Acceptance Scenarios**:

1. **Given** watchers are enabled and a task file changes externally, **When** the user is viewing that project, **Then** the UI reflects the new state within the defined freshness window and notes the update source/time.
2. **Given** watchers are unavailable, **When** the user triggers manual refresh, **Then** the UI reloads data, marks prior data as stale, and resolves the staleness indicator after successful fetch.

---

### User Story 4 - Search, navigation, and pack/config awareness (Priority: P3)

Power users can quickly find entities across projects, navigate via saved filters or a command palette, and inspect pack/config information with safe, bounded edits where allowed.

**Why this priority**: Efficient navigation and transparent configuration reduce friction and mistakes as scope grows.

**Independent Test**: Use search/filters to locate a task across projects; open pack/config views; attempt a permitted config change with preview/rollback; confirm navigation shortcuts work on desktop and mobile.

**Acceptance Scenarios**:

1. **Given** multiple projects with many tasks and sessions, **When** the user searches by ID/title or applies filters, **Then** relevant items appear within the defined response time and can be opened directly.
2. **Given** a supported config field, **When** the user previews and confirms an edit, **Then** the change applies with backup/rollback recorded and an audit note; unsupported edits are blocked with guidance.

---

[Add more user stories as needed, each with an assigned priority]

### Edge Cases

- No Edison projects found or scan roots are inaccessible; UI must surface guidance to add roots or fix permissions without crashing.
- Edison files are corrupted/missing (e.g., incomplete QA round, malformed state); UI should present partial data with clear warnings and avoid speculative fixes.
- Large projects (10k+ tasks, many sessions) must remain navigable with pagination/search without timeouts.
- Concurrent CLI actions modify the same entity while UI is open; the UI must reconcile without overwriting external changes and show the most recent state.
- Watchers/notifications unavailable (OS limits, network disabled); polling/manual refresh must keep data accurate with visible staleness indicators.
- Sensitive data (paths, environment) must never leak in UI outputs or audit logs.

### Assumptions & Dependencies

- Users have local access rights to the project roots and can configure scan paths.
- Edison project structures exist on disk and remain the source of truth for state.
- File watching may be limited by the host OS; polling/manual refresh is always available as fallback.
- Actor identity for writes defaults to the local OS user with a required per-session display name to keep audit entries trustworthy without adding multi-user auth scope.

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: The system MUST detect Edison projects from configured scan roots, allow pinning/unpinning specific paths, and present per-project health (counts of tasks, sessions, QA, recent activity) on load.
- **FR-002**: The system MUST provide project detail views that list and filter tasks, sessions, QA rounds, and agents/validators with clear loading, error, and empty states.
- **FR-003**: The system MUST show full detail for a selected task/session/QA round, including status, history, related entities, and evidence links without requiring external tools.
- **FR-004**: The system MUST let users initiate guarded writes (create/edit/transition tasks and sessions; trigger validations) only after a preview/confirmation step and MUST block invalid actions with the guard reason.
- **FR-005**: The system MUST record an audit entry for every state-changing action with actor (derived from local OS user plus required per-session display name), time, action, outcome, and context, and expose these entries in the UI.
- **FR-006**: The system MUST refresh data automatically when filesystem changes are observed and provide manual refresh/polling controls with visible freshness timestamps and staleness indicators.
- **FR-007**: The system MUST reconcile external changes (e.g., CLI edits) without overwriting them, always reflecting filesystem truth and signaling when data was updated externally.
- **FR-008**: The system MUST surface validation progress and results, including per-round verdicts and evidence, and allow re-runs from the UI where supported.
- **FR-009**: The system MUST offer search and saved filters across projects, tasks, sessions, and QA, returning results within defined performance targets and enabling direct navigation.
- **FR-010**: The system MUST provide pack/config visibility and allow bounded, reversible edits on an allowlist with backups and rollback guidance; unsupported edits must be declined with rationale.
- **FR-011**: The system MUST deliver responsive, accessible experiences on mobile and desktop, including keyboard navigation and clear focus/error states.
- **FR-012**: The system MUST avoid exposing secrets or sensitive paths in UI output or logs and confine operations to declared project roots.

### Key Entities *(include if feature involves data)*

- **Project**: A discovered Edison project with metadata (name/path), health counts, last activity, and pin status.
- **Session**: A unit of Edison work with state, history, linked tasks, and optional git/worktree info.
- **Task**: A work item with status, description, tags, timestamps, and related QA/validation data.
- **QA Round**: Validation evidence and verdicts associated with a task, including round status and artifacts.
- **Agent/Validator**: Edison-provided automation entries, displayed for visibility and selection where applicable.
- **Audit Entry**: Record of a state-changing action including actor, timestamp, action type, outcome, and context.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: Project discovery displays all accessible projects with health summaries in under 10 seconds for up to 100 projects and reports inaccessible roots instead of failing.
- **SC-002**: Task/session/QA lists render within 2 seconds for datasets up to 10,000 items with no more than 1% request failure rate across a 30-minute test window.
- **SC-003**: 100% of state-changing actions (create/edit/transition/trigger validation) generate audit entries visible in the UI within 5 seconds of completion.
- **SC-004**: Guarded actions prevent invalid transitions with clear reasons in 95% of negative test cases, and successful transitions reflect on-screen within 5 seconds.
- **SC-005**: Realtime or polling updates reflect external filesystem changes in under 5 seconds when watchers are available and under 30 seconds when falling back to polling/manual refresh.
- **SC-006**: At least 90% of pilot users can locate a specific task or session across projects via search/filtering and open its detail view in under 30 seconds during usability testing.
