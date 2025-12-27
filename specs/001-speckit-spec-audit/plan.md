# Implementation Plan: Edison UI Speckit Audit & Consolidation

**Branch**: `001-speckit-spec-audit` | **Date**: 2025-12-20 | **Spec**: specs/001-speckit-spec-audit/spec.md
**Input**: Feature specification from `/specs/001-speckit-spec-audit/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Provide Speckit-aligned specification and planning assets for Edison UI, focused on: near-zero-setup startup, a sidebar navigation shell, board-first + keyboard-first Tasks/Sessions workspace (including hierarchy and “ready/blocked” explanations), QA as a primary flow, guarded writes with audits, push-first realtime subscriptions (with polling fallback), and safe remote mobile access via pairing/auth. Technical approach remains local-first: filesystem is the source of truth; guarded writes respect Edison state machines with previews/audit trails; freshness via watchers feeding push updates with polling fallback; actor identity is the local OS user plus per-session display name.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript/Next.js 14 (frontend)  
**Primary Dependencies**: FastAPI, Pydantic, Next.js App Router, Tailwind, Vitest/RTL, Playwright  
**Storage**: Local filesystem Edison project structure (source of truth); no external DB  
**Testing**: pytest + FastAPI TestClient; Vitest + RTL; Playwright for journeys  
**Target Platform**: Web-first (desktop + mobile browsers); localhost by default with opt-in network-exposed mode (paired/authenticated)  
**Project Type**: Web (frontend + backend)  
**Performance Goals**: Discovery <10s for 100 projects; list views <2s for 10k items; UI freshness <5s (watchers) / <30s (poll/manual)  
**Constraints**: Local-first, safe-guarded writes; avoid secret/path leaks; responsive and accessible; push/watchers may be unavailable so polling/manual refresh required; remote access must be opt-in and authenticated  
**Scale/Scope**: Up to 100 projects; 10k+ tasks per project; 100+ concurrent WebSocket connections target

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Edison Constitutions** (`.edison/_generated/constitutions/`):
- ✅ TDD (NON-NEGOTIABLE): RED→GREEN→REFACTOR cycle enforced
- ✅ No Mocks: Real behavior testing; mock only at system boundaries
- ✅ Configuration-First: All config from YAML, no hardcoded values
- ✅ Git Safety: No branch switching in primary checkout; no destructive commands

**Project Constitution** (`.specify/memory/constitution.md` v1.0.0):
- ✅ Filesystem-First: Edison files are source of truth
- ✅ Safe Guarded Writes: Preview/confirm, guards enforced, audit entries
- ✅ Privacy/Redaction: Sensitive data never leaks
- ✅ Accessibility: Keyboard nav, ARIA, responsive design

**Technical Constraints Verified**:
- ✅ Stack: Python 3.13 + FastAPI / TypeScript + Next.js 14 + Tailwind v4
- ✅ Performance: Discovery <10s, list <2s, push <5s, poll <30s
- ✅ Pagination: >100 items paginate, >500 virtualize
- ✅ Remote Access: Localhost default, exposed requires pairing

**Quality Gates** (per constitution):
- Before implementation: Spec reviewed, plan approved, contracts defined
- Before PR: Tests pass, coverage ≥90%, no TODOs, type-safe, accessible
- Before release: E2E pass, performance verified, security reviewed

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── api/                # FastAPI routers
│   ├── router.py       # Main API router
│   └── routes/         # Route modules
│       └── health.py   # Health check endpoint
├── core/               # Backend settings + shared utilities
│   └── settings.py     # Configuration via environment
├── models/             # Pydantic models (to be created: T004)
├── services/           # Business logic services (to be created: T005)
├── main.py             # FastAPI app entrypoint
└── tests/              # pytest
    ├── conftest.py     # Test fixtures
    └── test_health.py  # Health check tests

frontend/
├── app/                # Next.js App Router routes
│   ├── layout.tsx      # Root layout
│   ├── page.tsx        # Home page
│   ├── globals.css     # Global styles
│   └── projects/       # Project-related routes (to be expanded)
├── components/         # Shared UI components
│   ├── AppHeader.tsx   # Navigation header
│   └── AppHeader.test.tsx
├── test/               # Vitest setup/utilities
│   └── setup.ts        # Test configuration
└── vitest.config.ts    # Vitest configuration

```

**Structure Decision**: Use the existing web split with `backend/` (FastAPI) and `frontend/` (Next.js). Tests live under each project. Additional directories (`models/`, `services/`, `lib/`) will be created as needed during Phase 2 implementation.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| _None_ | | |
