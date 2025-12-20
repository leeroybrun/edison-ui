# Edison UI - Quick Start

**Last updated**: 2025-12-20

## Prerequisites

- Python 3.11+ (backend). If your `python3` is 3.14, prefer `python3.13` (wheels support).
- Node.js 20+ (frontend)
- Edison CLI available on PATH (for development workflows)

## Setup

```bash
make install            # uses PYTHON=python3.13 by default
# or: make install PYTHON=python3.13
```

Optional (recommended for development): install Edison from the sibling repo.
```bash
make install-edison EDISON_PATH=../edison
```

## Run (two terminals)

```bash
make dev-backend
```

```bash
make dev-frontend
```

- Frontend: `http://localhost:3000`
- Backend health: `http://localhost:8000/api/v1/health`

## Tests

```bash
make test
```
