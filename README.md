# Edison UI

Local-first dashboard for Edison projects (FastAPI + Next.js).

## Overview

Edison UI provides a visual, mobile-friendly way to browse Edison projects on a machine. v0.1 focuses on **read-only** visibility (projects, tasks, sessions, QA, agents/validators).

## Architecture

- Backend: FastAPI (Python) reading Edison state via Edison APIs/files
- Frontend: Next.js (App Router) + TypeScript + Tailwind
- Source of truth: Edison project files (`.edison/`, `.project/`)

## Quick Start

```bash
make install            # uses PYTHON=python3.13 by default
make dev-backend   # terminal 1
make dev-frontend  # terminal 2
```

## Project Structure

```
edison-ui/
├── backend/          # FastAPI backend server
├── frontend/         # Next.js frontend application
├── .specify/         # Spec-kit specifications
├── .edison/          # Edison configuration
```

## Development

Specs live under `.specify/specs/edison-ui/` (v0.1 is read-only by default).

See `.specify/specs/edison-ui/quickstart.md` for details.
