# Quick Start — Edison UI Speckit Audit & Consolidation

## Prereqs
- Python 3.13, Node.js 20+
- Edison project(s) available locally

## Install
```bash
make install            # backend + frontend deps
```

## Run (two terminals)
```bash
make dev-backend
make dev-frontend
```
- Backend: http://localhost:8000/api/v1/health  
- Frontend: http://localhost:3000

## Test
```bash
make test
```

## Feature Focus
- Verify “zero setup” first-run flow (scan roots) and dashboard health for local Edison projects.
- Validate the sidebar navigation shell (Dashboard / Sessions / Tasks / QA / Agents / Settings).
- Validate Tasks & Sessions list/board views, session filtering in Tasks, hierarchical expand/collapse, and keyboard-first navigation.
- Validate QA as a primary flow: per-task validation status, rounds, evidence, and validator details.
- Confirm push-first realtime updates when available; fall back to manual refresh/polling when unavailable.
- Validate remote mobile access (opt-in) pairing/auth flow and unauthenticated request rejection in remote mode.
- Validate worker visibility via tracking: active implementation/validation runs + tracked processes (when available).
