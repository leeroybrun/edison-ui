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
- Verify project discovery shows health for local Edison projects.
- Exercise guarded writes (create/transition tasks and sessions) with previews and audit entries.
- Confirm freshness via watchers; fall back to manual refresh/polling when watchers unavailable.
- Validate search/navigation and pack/config visibility behave per spec.
