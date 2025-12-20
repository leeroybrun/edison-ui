# Edison UI - Functional Specification (Fully Featured v1 Target)

**Status**: Draft (v1 target with incremental milestones)  
**Last updated**: 2025-12-20

## Summary

Edison UI is a local-first, mobile-friendly dashboard for managing Edison projects on a machine: discover projects, follow the full workflow lifecycle, and operate Edison safely (sessions/tasks/QA/validations/agents/validators/config), with progressive enhancement from read-only to full “safe parity” with Edison CLI.

## North Star (v1.0)

From the UI (desktop + mobile), a developer can:
- discover and manage multiple Edison projects
- start and steer sessions (worktrees) and tasks end-to-end
- view and act on QA/validation rounds (including evidence)
- browse and tune packs / agents / validators and delegations
- search across everything and understand “what’s happening now”
- do all of the above safely (guardrails, confirmations, audit trail) and correctly (filesystem truth, state machine compliance)

## Design Principles

1) **Filesystem as truth**: `.edison/`, `.project/`, and git worktrees are authoritative.  
2) **Edison-first integration**: use Edison public Python APIs; CLI is a boundary fallback (explicit and allowlisted).  
3) **Safety-first operations**: destructive actions require preview + confirmation + reversible path when possible.  
4) **Incremental delivery**: ship useful read-only visibility early, then layer writes, realtime, and advanced tooling.  
5) **Mobile parity**: mobile supports monitoring + light operations; desktop supports dense power-user workflows.

## Definitions / Terminology

- **Project**: a directory containing `.edison/` (and typically `.project/`).  
- **Task**: an Edison task record (status in `todo|wip|blocked|done|validated`).  
- **Session**: an Edison session record (state includes: `draft|active|blocked|done|closing|validated|recovery|archived`).  
- **QA**: Edison QA record(s) tied to a task, including validator rounds and evidence artifacts.  

## Feature Areas (v1)

### 1) Project Discovery + Dashboard
- Discover projects from configured scan roots + manual add/remove pins.
- Per-project health: active sessions, WIP tasks, validations pending/failing, last activity.
- Recent activity timeline across projects (filterable).

### 2) Sessions (Full lifecycle)
- Create sessions (with or without explicit session ID).
- Show session state, history, and available transitions (with guard explanations).
- Worktree visibility: path, base branch, status, dirty state.
- Pause/stop/close workflows where Edison supports it; otherwise provide safe CLI fallback.

### 3) Tasks (Workflow + hierarchy)
- Kanban + table views; filters by owner/session/status/tags.
- Task detail: markdown rendering, attachments/links, dependency graph, parent/children.
- Task CRUD: create/edit/close/split/duplicate (where supported).
- Delegation tracking: show which agent(s) were used, their outputs, and follow-ups.

### 4) QA / Validation Hub
- QA list: state, latest verdict, validators involved, last run, next actions.
- Round browser: per-round findings, evidence files, pass/fail with rationale.
- Re-run validation (manual triggers) and show validator wave progress.
- Export: JSON and “bundle view” summary for sharing.

### 5) Agents / Validators / Packs
- Browse generated agents and validators, their triggers, blocking vs advisory, and waves.
- Visualize delegation rules and “why this agent/validator ran”.
- Pack manager: enable/disable packs and view pack-provided overlays safely.
- (v1) limited configuration edits with schema validation and rollback.

### 6) Search + Navigation
- Global search across tasks/sessions/QA/validators (IDs + text).
- Saved filters and quick scopes (per project and global).

### 7) Git Integration (UI assists, Edison remains source)
- Read: status, branches, commits for a session worktree.
- Link commits to tasks (heuristics + manual linking).
- Write: only safe operations with confirmations (commit with message template; push/pull optional).

### 8) Terminal / Command Palette (bounded)
- Command palette for common actions (create session, claim task, open evidence).
- Embedded terminal is optional and should be bounded (or disabled by default); the UI must remain safe.

### 9) Realtime + Notifications
- Realtime updates from filesystem watchers → backend push to UI.
- Notifications: in-app; optional desktop notifications (opt-in).
- Presence/collaboration is deferred unless/until multi-user is in-scope.

### 10) Analytics (local-first)
- Basic metrics: time in state, validation pass rate, WIP aging, bottlenecks.
- Everything is opt-in; no external telemetry by default.

## UX Requirements

- Responsive layout:
  - Mobile: single-column, bottom navigation, progressive disclosure.
  - Desktop: dense views, split panes, keyboard shortcuts.
- Accessibility: semantic HTML, keyboard navigation, visible focus, reasonable contrast.
- “Dangerous” actions have consistent UX: preview → confirm → execute → show outcome + audit entry.

## Correctness Requirements

- State transitions must comply with Edison state machines (no “UI-only” shortcuts).
- Concurrent CLI usage must be handled:
  - explicit refresh always available
  - polling fallback when realtime is unavailable
  - eventual realtime push (watchers) does not “invent” state

## Milestones (incremental delivery)

- **v0.1 (read-only MVP)**: discover + browse projects/tasks/sessions/QA/agents/validators with refresh/polling.
- **v0.2 (safe writes)**: create + transition tasks/sessions with confirmations + audit trail.
- **v0.3 (realtime)**: file watchers + push updates, baseline notification UX.
- **v0.4 (config/packs)**: pack browser/manager + safe config editing with schema validation + rollback.
- **v1.0 (fully featured)**: end-to-end parity for common Edison workflows + analytics + power-user UX.
