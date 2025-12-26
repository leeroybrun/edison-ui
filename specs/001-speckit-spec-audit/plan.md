# Implementation Plan: Edison UI Speckit Audit & Consolidation

**Branch**: `001-speckit-spec-audit` | **Date**: 2025-12-20 | **Spec**: specs/001-speckit-spec-audit/spec.md
**Input**: Feature specification from `/specs/001-speckit-spec-audit/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Provide Speckit-aligned specification and planning assets for Edison UI, focused on: near-zero-setup startup, a sidebar navigation shell, board-first + keyboard-first Tasks/Sessions workspace (including hierarchy and “ready/blocked” explanations), QA as a primary flow, guarded writes with audits, push-first realtime subscriptions (with polling fallback), and safe remote mobile access via pairing/auth. Technical approach remains local-first: filesystem is the source of truth; guarded writes respect Edison state machines with previews/audit trails; freshness via watchers feeding push updates with polling fallback; actor identity is the local OS user plus per-session display name.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

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

Project constitution file `.specify/memory/constitution.md` is placeholder-only (no enforceable rules). Default engineering guardrails apply (local-first safety, TDD, no mocks philosophy from Edison agent constitution). No explicit project-level gates violated; proceed.

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
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

```

**Structure Decision**: Use the existing web split with `backend/` (FastAPI) and `frontend/` (Next.js). Tests live under each project.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| _None_ | | |
