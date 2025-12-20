# Research Findings — Edison UI Speckit Audit & Consolidation

## 1) Actor identity for writes and auditing
- **Decision**: Actor = local OS user; require per-session display name stored with each audit entry.
- **Rationale**: Keeps audit trail trustworthy without adding multi-user auth scope; aligns with local-first model and avoids blocking workflows on credentialing.
- **Alternatives considered**: Generic “local user” (too weak for accountability); local passphrase gate (adds friction without multi-user support); full auth (over-scopes current feature).

## 2) Freshness and concurrency strategy
- **Decision**: Prefer filesystem watchers for realtime updates; fall back to polling/manual refresh with visible freshness timestamps and staleness indicators.
- **Rationale**: Edison is filesystem-first; watchers provide timely updates, but polling/manual refresh ensures reliability on constrained hosts.
- **Alternatives considered**: Polling only (risks staleness/perf hit); watcher-only (breaks on limited OS permissions); optimistic-only UI (risks drift vs filesystem truth).

## 3) Guarded writes and audit coverage
- **Decision**: All state-changing actions require preview/confirmation, enforce Edison guards, and emit audit entries with actor/time/action/outcome/context.
- **Rationale**: Prevents unsafe transitions, captures accountability, and matches safety-first requirements.
- **Alternatives considered**: Direct writes without preview (unsafe, conflicts with guards); partial auditing (creates blind spots); soft warnings on guard failures (insufficient protection).

## 4) Data shape and scope
- **Decision**: Treat filesystem Edison artifacts as canonical: Project → Sessions/Tasks/QA → Agents/Validators; no external DB; support up to 100 projects and 10k+ tasks/project.
- **Rationale**: Mirrors existing Edison model, minimizes complexity, and aligns with performance targets in the spec.
- **Alternatives considered**: Introduce DB/cache layer (over-scopes current goal); limit scale assumptions (would undercut success criteria).
