<!--
  Sync Impact Report
  ===================
  Version change: 0.0.0 (placeholder) → 1.0.0 (initial)

  Modified principles: N/A (initial creation)

  Added sections:
  - Core Principles (7 principles)
  - Technical Constraints
  - Quality Gates
  - Governance

  Removed sections: N/A (initial creation)

  Templates status:
  - .specify/templates/plan-template.md: ✅ Compatible (Constitution Check section exists)
  - .specify/templates/spec-template.md: ✅ Compatible (no constitution-specific sections)
  - .specify/templates/tasks-template.md: ✅ Compatible (phase structure aligns)

  Follow-up TODOs: None
-->

# Edison UI Constitution

## Core Principles

### I. Filesystem-First (Source of Truth)

Edison project files (`.edison/`, `.project/`) are the canonical source of truth for all state. The UI MUST:
- Read all state from Edison filesystem artifacts
- Never maintain a parallel database for Edison state
- Reconcile external changes (CLI, other agents) without overwriting
- Prefer filesystem watchers for freshness; fall back to polling/manual refresh

**Rationale**: Edison is filesystem-first by design. The UI is a window into that state, not an alternative store.

### II. Test-Driven Development (NON-NEGOTIABLE)

All implementation work MUST follow the RED-GREEN-REFACTOR cycle:
- **RED**: Write a failing test first; confirm it fails for the right reason
- **GREEN**: Add minimum code to pass the test—no speculative features
- **REFACTOR**: Improve code with all tests green; rerun full suite

No production code without a failing test first. Coverage targets: overall >= 90%, changed/new code >= 100%.

**Rationale**: TDD ensures correctness, prevents regressions, and documents behavior.

### III. No Mocks (Real Behavior Testing)

Test real behavior, not mocked behavior. Mocking internal code means testing nothing:
- Use real filesystem (tmp directories)
- Use real HTTP (TestClient, fetch)
- Use real database connections (test isolation strategies)
- Mock only at system boundaries (external third-party APIs)

**Rationale**: Real tests catch real bugs; mocked tests only prove the mock works.

### IV. Safe Guarded Writes

All state-changing actions from the UI MUST:
- Require preview/confirmation before applying
- Enforce Edison guard rules (state machine transitions)
- Emit audit entries with actor (OS user + display name), time, action, outcome
- Block invalid transitions with clear reasons

**Rationale**: Edison's guard system protects workflow integrity; UI writes must respect it.

### V. Configuration-First

No hardcoded values. All configuration comes from YAML (Edison config hierarchy):
- Thresholds, timeouts, feature flags, endpoints
- Pagination limits, freshness intervals, redaction patterns
- Default (code) → Core YAML → Pack YAML → Project YAML → Environment

**Rationale**: Enables environment-specific behavior without code changes.

### VI. Privacy and Redaction

Sensitive data MUST never leak in UI output, logs, or audit entries:
- Absolute paths outside configured project roots
- Environment variables and credentials
- API keys and tokens
- Private user data

Redaction rules MUST be applied at the API boundary before data reaches the frontend.

**Rationale**: Local-first does not mean insecure; protect user data by default.

### VII. Accessibility and Responsiveness

The UI MUST be usable by all users across devices:
- Keyboard navigation for all core flows
- ARIA labels and focus states
- Mobile-first responsive design (Tailwind)
- Clear loading, error, and empty states

**Rationale**: Edison UI is "web-first"; accessibility is a first-class requirement.

## Technical Constraints

### Stack

- **Backend**: Python 3.13 + FastAPI
- **Frontend**: TypeScript + Next.js 14 (App Router) + Tailwind v4
- **Testing**: pytest (backend), Vitest + RTL (frontend), Playwright (E2E)
- **Storage**: No database; filesystem is source of truth

### Performance Targets

| Metric | Target |
|--------|--------|
| Project discovery (100 projects) | < 10 seconds |
| List/board render (10k items) | < 2 seconds |
| Push/watcher freshness | < 5 seconds |
| Polling/manual fallback freshness | < 30 seconds |
| Audit entry visibility after write | < 5 seconds |

### Pagination and Virtualization

- Lists with > 100 items MUST paginate
- Lists with > 500 items SHOULD virtualize
- Full content MUST NOT load until item is opened

### Remote Access

- Localhost-only by default
- Network-exposed mode is opt-in and MUST require pairing/auth
- Unpaired clients MUST be rejected with no sensitive data returned

## Quality Gates

### Before Implementation

- [ ] Spec reviewed and clarified
- [ ] Plan approved (architecture, data model)
- [ ] Contracts defined (API schemas)
- [ ] Tasks generated and dependency-ordered

### Before PR Merge

- [ ] All tests pass (RED→GREEN verified per task)
- [ ] Coverage >= 90% overall; 100% for changed files
- [ ] No TODO/FIXME in production code
- [ ] No console.log or debug statements
- [ ] Type-safe (no untyped escape hatches without justification)
- [ ] Accessibility checked (keyboard nav, ARIA)
- [ ] Redaction rules applied for sensitive data

### Before Release

- [ ] E2E journeys pass (Playwright)
- [ ] Performance targets met (measured)
- [ ] Quickstart validated (fresh setup works)
- [ ] Security review (remote access, auth, pairing)

## Governance

This constitution supersedes all other practices within the Edison UI project scope.

### Amendment Process

1. Propose amendment with rationale
2. Review impact on existing artifacts (spec, plan, tasks)
3. Approval required before merge
4. Update version per semantic versioning:
   - **MAJOR**: Principle removal or redefinition
   - **MINOR**: New principle or section added
   - **PATCH**: Clarification or wording fix
5. Propagate changes to dependent templates

### Compliance

- All PRs MUST verify compliance with this constitution
- Complexity beyond these constraints MUST be justified in plan.md
- Constitution conflicts are CRITICAL and block implementation

**Version**: 1.0.0 | **Ratified**: 2025-12-27 | **Last Amended**: 2025-12-27
