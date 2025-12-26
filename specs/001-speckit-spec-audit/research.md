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

## 5) Push-first realtime subscriptions
- **Decision**: Use a push-first subscription model for realtime updates (snapshot + incremental updates) when available; retain polling/manual refresh fallback.
- **Rationale**: Reduces load vs repeated full refetches, improves perceived responsiveness, and scales better to large task sets while keeping a reliable fallback path.
- **Alternatives considered**: Polling-only (wasteful at scale); watcher-only without push (harder to keep multiple clients in sync); notify-then-fetch (more race-prone and higher request volume).

## 6) Remote access safety (pairing/auth)
- **Decision**: Remote access is opt-in. When the server is network-exposed, require a pairing/auth flow; localhost-only mode remains the safe default.
- **Rationale**: Enables mobile access without accidentally exposing sensitive local data on the LAN.
- **Alternatives considered**: Always bind to all interfaces (unsafe by default); no auth on LAN (too risky); full multi-user auth (over-scopes current feature).

## 7) Board-first and keyboard-first UX
- **Decision**: Provide board and list views for Tasks and Sessions, with keyboard-first navigation and a persistent sidebar shell.
- **Rationale**: Matches power-user workflow needs and makes “what’s ready/blocked/in progress” instantly visible.
- **Alternatives considered**: List-only UI (slower scanning); mouse-first interactions (slower for heavy users); session-only task visibility (hides global tasks and reduces usefulness).

## 8) QA as a primary pipeline flow
- **Decision**: Make QA/validation status visible in task lists/boards and provide a dedicated QA view plus rich per-task QA detail.
- **Rationale**: Edison’s validation pipeline is core; UI should make it obvious and navigable.
