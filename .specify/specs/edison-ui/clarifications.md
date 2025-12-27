# Edison UI - Clarifications (v0.1 → v1.0)

**Status**: Draft  
**Last updated**: 2025-12-20

## Auth / Multi-user
- v0.1–v1.0 are single-user local-first by default.
- If the backend is bound to a network interface later, add opt-in auth at the boundary (post-v1 unless required earlier).

## Project discovery defaults
- Scan roots are configurable; defaults should be conservative (explicit roots > full home scan).
- Ignore dirs: `node_modules`, `.git`, `dist`, `build`, `.next`, `venv`, `.venv`.
- Max depth is configurable; default should avoid expensive scans.

## IDs
- `projectId` is derived from absolute path (hash) and is opaque in the API.
- Session/task IDs remain Edison IDs (`session-*`, `task-*`).

## Safety model for writes
- v0.2+ adds writes behind consistent UX gates: preview → confirm → execute → audit entry.
- “Force” overrides (bypassing guards) are not supported unless Edison supports it explicitly; otherwise UI remains safe-by-default.

## CLI fallback policy
- Preferred: Edison public Python APIs.
- If CLI fallback is required:
  - only allowlisted subcommands
  - explicit project root and session/worktree confinement
  - capture stdout/stderr and surface it in the UI + audit log

## Realtime / concurrent CLI usage
- Filesystem is the source of truth.
- v0.1 uses explicit refresh + optional polling.
- v0.3 introduces watchers + push; the UI reconciles without becoming authoritative.
