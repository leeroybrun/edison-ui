# Feature Specification: Edison UI Speckit Audit & Consolidation

**Feature Branch**: `001-speckit-spec-audit`  
**Created**: 2025-12-20  
**Status**: Draft  
**Input**: User description: "please analyse ALL the files in this repository, and all the files in /Users/leeroy/Documents/Development/edison-ui/.specify as well, which have been created by claude code manually and then updated by codex. and check if they are correct speckit artifacts/files, otherwise create a real and comprehensive speckit spec from them"

## Clarifications

### Session 2025-12-20

- Q: What actor identity should be recorded for guarded writes and audit entries? → A: Use the local OS user as actor and require an explicit per-session display name for audit logs.
- Q: Should Edison UI be usable remotely (mobile)? → A: Yes — web app first; remote access must be safe by default (opt-in network exposure + pairing/auth).

### Session 2025-12-27 (Analysis-Driven Clarifications)

- Q: What are "memory providers" and how do they integrate with Edison UI?
  → A: Memory providers are optional integrations that store/search long-lived information across sessions. Edison supports multiple provider types:
    - **ExternalCliMemoryProvider**: CLI tools returning JSON (e.g., episodic-memory)
    - **McpToolsMemoryProvider**: MCP servers exposing search tools
    - **GraphitiPythonMemoryProvider**: Python async memory classes
    - **FileStoreMemoryProvider**: Local file-based fallback (patterns.md, gotchas.md, codebase_map.json)
  The UI should surface memory search when `memory.enabled=true` in Edison config and degrade gracefully when disabled or unavailable. Memory is fail-open: failures never break core workflows.

- Q: What entities are session-scopable for the "global view + session filter" pattern (FR-014a)?
  → A: At minimum: Tasks, QA, and Tracking Runs (agents/validators). The pattern means:
    - A global view shows all entities across the project
    - Session detail shows the same component filtered by `sessionId`
    - Both views are functionally equivalent—session detail is just a pre-applied filter

- Q: What constitutes "sensitive data" for redaction (FR-012)?
  → A: The following categories MUST be redacted at the API boundary:
    - Absolute filesystem paths outside configured project roots
    - Environment variable values (keys may be shown)
    - API keys, tokens, and credentials
    - Private user data (email, identifiers) unless actor identity

- Q: What are the pagination/virtualization thresholds for "large" artifacts?
  → A: Per constitution:
    - Lists with > 100 items MUST paginate (server-side)
    - Lists with > 500 items SHOULD virtualize (client-side windowing)
    - Full content (task body, evidence files) MUST NOT load until item is opened

- Q: What evidence artifact types exist and how are they handled?
  → A: Evidence lives under `.project/qa/validation-evidence/<task-id>/round-<n>/` and includes:
    - `bundle-summary.md` — structured round summary
    - `implementation-report.md` — agent implementation report
    - `validator-<id>-report.md` — per-validator reports
    - Command outputs, coverage files, screenshots (configured per project)
  The UI should display markdown inline (with redaction) and link to other artifacts for download/preview.

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
-->

### User Story 1 - Zero-setup project dashboard + navigation shell (Priority: P1)

Developers can start Edison UI with near-zero setup and immediately see every Edison project on the machine with its health, active work (tasks, sessions, QA), and recent activity in one place, within a persistent sidebar-driven navigation shell.

**Why this priority**: This is the primary value of the UI—fast, trustworthy awareness without needing the CLI.

**Independent Test**: Start the UI with multiple sample Edison projects present; confirm first-run setup works, then users can discover projects, open one, and inspect read-only details.

**Acceptance Scenarios**:

1. **Given** the user has not configured Edison UI before, **When** they start the UI, **Then** they are guided to select scan roots (or accept safe defaults) and reach the dashboard without editing config files.
2. **Given** configured scan roots include two Edison projects, **When** the user opens the dashboard, **Then** both projects appear with status, last activity, and counts for tasks/sessions/QA.
3. **Given** a project with tasks, sessions, QA rounds, and agent/validator metadata on disk, **When** the user opens that project, **Then** they can view lists and detail pages for each entity with clear loading/error/empty states.

---

### User Story 2 - Board-first + keyboard-first Tasks & Sessions workspace (Priority: P1)

Developers can quickly understand work state via board-first views and keyboard-first navigation, including:
- A project-wide Tasks view that includes tasks inside sessions and tasks outside sessions.
- A Sessions view (list + board), where selecting a session shows that session’s tasks using the same filtering semantics as the project-wide Tasks view.
- The same “global view + session filter + session details reuse” pattern for other session-scoped entities (QA and Agents/Validators).
- A hierarchical task list option that supports parent/child expand/collapse for subtasks.
- A “Ready” column that is actually ready, and “Blocked” explanations that are clear and actionable when dependency/guard information is available.

**Why this priority**: Edison projects grow large; power users need the fastest possible way to answer “what’s blocked/ready/in progress, and why?” and to drill into details.

**Independent Test**: In a project fixture with global tasks and session tasks (including parent/child and dependency metadata), use the sidebar to navigate between Sessions and Tasks, switch between list/board, filter tasks by session, and open task detail using only the keyboard.

**Acceptance Scenarios**:

1. **Given** a project has tasks both inside and outside sessions, **When** the user opens the project Tasks view, **Then** all tasks are visible (not only session-attached tasks) and can be filtered by session (including “No session”).
2. **Given** a session has tasks, **When** the user views that session’s tasks, **Then** the set of tasks matches filtering by that same session in the project Tasks view.
3. **Given** a session has tasks with parent/child relationships, **When** the user views that session’s tasks in list view, **Then** they can expand/collapse parent tasks to reveal child tasks without losing sorting/filtering.
4. **Given** the task board is displayed, **When** the user focuses the board and uses keyboard navigation, **Then** they can move between columns/cards, open a task, and return to the board without using the mouse.
5. **Given** task dependency metadata exists, **When** the board renders “Ready” and “Blocked”, **Then** “Ready” reflects actual readiness (dependencies satisfied and guards allow progress) and “Blocked” provides “why blocked” explanations.
6. **Given** a session has QA activity and agent/validator activity, **When** the user opens that session from Sessions view, **Then** they can access the session-scoped QA and Agents information from the session details, and the same data is visible from the global QA/Agents views by filtering to that session.

---

### User Story 3 - QA as a primary pipeline flow (Priority: P1)

Developers can view, monitor, and understand Edison validations/QA as a first-class workflow: task validation status is visible in lists/boards, and task detail clearly shows rounds, validators, verdicts, reasons, and evidence artifacts.

**Why this priority**: Validation is a core value proposition of Edison; users should not have to “hunt for QA” or rely on CLI-only visibility.

**Independent Test**: With a project fixture containing multiple QA rounds (pass/fail/in-progress) and evidence artifacts, open tasks from the board/list and verify validation status, rounds, evidence, and validator details.

**Acceptance Scenarios**:

1. **Given** a task has validation rounds and evidence, **When** the user opens task detail, **Then** they can see each round’s verdict/status, which validator(s) ran, the reasons for failures, and links to evidence artifacts (with safe redaction).
2. **Given** tasks have mixed validation states, **When** a tasks list/board is displayed, **Then** validation status is visible at-a-glance and can be filtered (e.g., “Needs validation”, “Rejected”, “Validated”).
3. **Given** a validation is in progress, **When** the user is viewing the task or QA view, **Then** progress is visible and updates as new validator results arrive.

---

### User Story 4 - Safe, guarded actions with previews + audits (Priority: P2)

Developers can create or transition tasks and sessions, and trigger validations, with previews, guard explanations, and audit entries so changes are safe and reversible.

**Why this priority**: Teams need to act from the UI, but every write must respect Edison rules and capture who/what/when.

**Independent Test**: In a project fixture, attempt a session transition and a task creation from the UI; verify previews, confirmations, successful writes, and recorded audit entries; verify invalid transitions are blocked with reasons.

**Acceptance Scenarios**:

1. **Given** a draft session, **When** the user requests a transition to active and confirms after reviewing guards, **Then** the session state changes, the UI updates, and an audit entry records actor/time/outcome.
2. **Given** a blocked task, **When** the user attempts an invalid transition, **Then** no file changes occur and the UI shows the guard failure reason and how to resolve it.

---

### User Story 5 - Push-first realtime updates with clear freshness (Priority: P2)

Users see timely updates caused by CLI activity or background processes via server push when available, with polling/manual refresh fallbacks and clear staleness indicators.

**Why this priority**: Edison state changes outside the UI; “push-first” reduces load and improves confidence at scale while keeping polling as a safety net.

**Independent Test**: With server push enabled, edit a task via CLI and confirm the UI updates without manual refresh; disable push/watchers and confirm polling/manual refresh restores freshness with visible timestamp/status cues.

**Acceptance Scenarios**:

1. **Given** push updates are enabled and a task file changes externally, **When** the user is viewing that project, **Then** the UI reflects the new state within the defined freshness window and notes the update source/time.
2. **Given** push updates are unavailable, **When** the user triggers manual refresh, **Then** the UI reloads data, marks prior data as stale, and resolves the staleness indicator after successful fetch.

---

### User Story 6 - Remote mobile access with pairing (Priority: P2)

Developers can safely access Edison UI from a mobile phone on the same network (or via a reverse proxy) using an explicit pairing flow, without accidentally exposing sensitive local data.

**Why this priority**: “Web app first” is a key goal, but network exposure must be explicit and safe.

**Independent Test**: Start the server in network-exposed mode, pair a second device, and confirm APIs/streams are inaccessible without auth and usable after pairing.

**Acceptance Scenarios**:

1. **Given** the server is bound only to localhost, **When** a second device attempts to access it, **Then** access fails and the UI explains how to enable remote mode.
2. **Given** the user enables remote mode, **When** they pair a device using a time-limited code/QR, **Then** the device receives authorized access and can browse projects, tasks, sessions, and QA.
3. **Given** an unpaired device attempts access, **When** it calls APIs or realtime streams, **Then** it is rejected and no sensitive data is returned.

---

### User Story 7 - Session context + memory + agent monitoring (Priority: P3)

Developers can monitor what sessions are doing by viewing “next” and “session context” outputs, search across entities and memory, and see which agents/validators are currently active.

**Why this priority**: When work is automated, operators need observability into agent intent (“what’s next”), current injected context (“what the model sees”), and live activity.

**Independent Test**: In a project fixture with a running session and recent memory, open session detail and verify next/context output is shown; open Agents view and see active workers; perform a search that returns tasks/sessions/memory hits.

**Acceptance Scenarios**:

1. **Given** a session has “next” and “context” outputs available, **When** the user opens the session detail page, **Then** they can view the latest outputs with timestamps and safe redaction.
2. **Given** agents/validators are currently working, **When** the user opens the Agents view, **Then** they can see active workers, which session/task they relate to, and last update/heartbeat.
   - Note: “active workers” SHOULD be derived from Edison tracking metadata + the append-only process events stream when available.
3. **Given** memory providers are configured, **When** the user searches for a concept, **Then** results include relevant tasks/sessions/QA and memory hits (clearly labeled by source).

## Edge Cases & Constraints

- Projects may be missing expected directories; UI must surface degraded health with actionable messages, not crash.
- Some Edison artifacts may be large; list views must paginate/virtualize and avoid loading full content until needed.
- Concurrent edits may occur (UI vs CLI); UI must prefer filesystem truth and never silently overwrite external changes.
- File watching / push streams may be unavailable; polling/manual refresh must always be supported.
- Actor identity must be stable and explicit for auditing (OS user + display name).
- Remote access must be opt-in; network-exposed mode must require authentication and must include clear warnings.
- Sensitive data (paths, environment) must never leak in UI outputs, logs, or audit entries.

## Assumptions & Dependencies

- Users have local access rights to the project roots and can configure scan paths.
- Edison project structures exist on disk and remain the source of truth for state.
- Edison CLI capabilities may expand (e.g., session context, memory providers). The UI should surface these capabilities when present and degrade gracefully when absent.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST detect Edison projects from configured scan roots, allow pinning/unpinning specific paths, and present per-project health (counts of tasks, sessions, QA, recent activity) on load.
- **FR-002**: The system MUST provide project views that list and filter tasks (including tasks not associated with any session), sessions, QA rounds, and agents/validators with clear loading, error, and empty states.
- **FR-003**: The system MUST show full detail for a selected task/session/QA round, including status, history, related entities, and evidence links without requiring external tools.
- **FR-004**: The system MUST let users initiate guarded writes (create/edit/transition tasks and sessions; trigger validations) only after a preview/confirmation step and MUST block invalid actions with the guard reason.
- **FR-005**: The system MUST record an audit entry for every state-changing action with actor (derived from local OS user plus required per-session display name), time, action, outcome, and context, and expose these entries in the UI.
- **FR-006**: The system MUST support push-first realtime updates (subscribe + snapshot + incremental updates) when available, and MUST provide polling/manual refresh fallbacks with visible freshness timestamps and staleness indicators.
- **FR-007**: The system MUST reconcile external changes (e.g., CLI edits) without overwriting them, always reflecting filesystem truth and signaling when data was updated externally.
- **FR-008**: The system MUST surface validation progress and results as a primary flow, including per-round verdicts, validator identities, reasons, and evidence, and allow re-runs from the UI where supported.
- **FR-009**: The system MUST offer search and saved filters across projects, tasks, sessions, QA, and memory (when configured), returning results within defined performance targets and enabling direct navigation.
- **FR-010**: The system MUST provide pack/config visibility and allow bounded, reversible edits on an allowlist with backups and rollback guidance; unsupported edits must be declined with rationale.
- **FR-011**: The system MUST deliver responsive, accessible experiences on mobile and desktop, including keyboard navigation, a persistent sidebar navigation shell, and clear focus/error states.
- **FR-012**: The system MUST avoid exposing secrets or sensitive paths in UI output or logs and confine operations to declared project roots.
- **FR-013**: The system MUST support a near-zero-setup start experience, including a first-run scan-root setup flow, a single-command local start option, and clear runtime status (host/port, last refresh).
- **FR-014**: The system MUST provide board and list views for Sessions and Tasks, with consistent filtering semantics between the project-wide Tasks view and per-session Tasks views.
- **FR-014a**: The system MUST apply the same “global view + session filter + session detail reuse” pattern to all entities that are or can be session-scoped (at minimum: Tasks, QA, Agents/Validators), so that session details views are consistent with filtering the corresponding global views by `sessionId`.
- **FR-015**: The system MUST explain readiness/blocking using dependency and guard information when available, and SHOULD include an at-a-glance “Ready/Blocked” breakdown for Tasks.
- **FR-016**: The system MUST support safe remote access by making network-exposed mode opt-in and requiring a pairing/auth flow for non-local clients.
- **FR-017**: The system MUST surface session operational context, including “next” and “session context” outputs when available, with timestamps and redaction.
- **FR-018**: The system MUST provide an Agents view that surfaces currently active agents/validators and their status/association to sessions/tasks, when such activity data is available.
- **FR-019**: The system SHOULD support hierarchical task presentation (parent/child) with expand/collapse.
- **FR-020**: The system SHOULD remain web-first and MAY provide an optional desktop wrapper (e.g., Tauri) that launches the same local web server and opens the UI.
- **FR-021**: The system MUST surface Edison core audit logs and session activity logs in a UX-friendly way, including a project-level Activity view and session/task-level timelines with filtering and drill-down (without exposing secrets).

### Key Entities *(include if feature involves data)*

- **Project**: A discovered Edison project with metadata (name/path), health counts, last activity, and pin status.
- **Session**: A unit of Edison work with state, history, linked tasks, and optional git/worktree info.
- **Task**: A work item with status, description, tags, timestamps, dependencies and hierarchy (parent/child), and related QA/validation data.
- **QA Round**: Validation evidence and verdicts associated with a task, including round status and artifacts.
- **Validator / Agent (catalog)**: Edison-provided validator/agent definitions (composed artifacts), displayed for visibility and selection where applicable.
- **Tracking Run**: Live/active work inferred from evidence tracking metadata and the append-only process events stream (implementation, validation, orchestrator).
- **Process Event**: Append-only JSONL event used to compute the live “tracked processes” index (started/heartbeat/completed/stopped).
- **Audit Entry**: Record of a state-changing action including actor, timestamp, action type, outcome, and context.
- **Audit Event**: Edison core structured audit event (append-only JSONL) with event type, timestamp, correlation ids (invocation/session), and optional tool/command details.
- **Realtime Subscription**: A client subscription for push updates (e.g., tasks list, session detail) including revisioning for stale-update protection.
- **Pairing Session**: A time-limited pairing handshake that grants authorized access for remote clients.
- **Session Context Payload**: Deterministic, hook-safe session/project context payload (rendered as markdown for humans, JSON for tooling).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Project discovery displays all accessible projects with health summaries in under 10 seconds for up to 100 projects and reports inaccessible roots instead of failing.
- **SC-002**: Task/session/QA lists and boards render within 2 seconds for datasets up to 10,000 items with no more than 1% request failure rate across a 30-minute test window.
- **SC-003**: 100% of state-changing actions (create/edit/transition/trigger validation) generate audit entries visible in the UI within 5 seconds of completion.
- **SC-004**: Guarded actions prevent invalid transitions with clear reasons in 95% of negative test cases, and successful transitions reflect on-screen within 5 seconds.
- **SC-005**: Push or polling updates reflect external filesystem changes in under 5 seconds when watchers/push are available and under 30 seconds when falling back to polling/manual refresh.
- **SC-006**: At least 90% of pilot users can locate a specific task or session across projects via search/filtering and open its detail view in under 30 seconds during usability testing.
- **SC-007**: First-run setup (scan roots + start) can be completed by 90% of pilot users in under 60 seconds without reading documentation.
- **SC-008**: In remote-access mode, 100% of unauthenticated API and realtime requests from unpaired clients are rejected in automated security tests, and pairing completes in under 60 seconds on a typical LAN.
