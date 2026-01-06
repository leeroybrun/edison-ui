#!/usr/bin/env bash
# Edison Web Server Stop Script for edison-ui
#
# Based on Edison core template: templates/scripts/web-server/stop-server.sh.template
#
# Stops the e2e test stack: FastAPI backend (port 8002) + Next.js frontend (port 3334)

set -euo pipefail

# <!-- SECTION: config -->
PROJECT_ROOT="${AGENTS_PROJECT_ROOT:-$(pwd)}"
MAIN_REPO_ROOT="${AGENTS_MAIN_REPO_ROOT:-$PROJECT_ROOT}"
SESSION_ID="${AGENTS_SESSION:-main}"

BACKEND_PORT=8002
FRONTEND_PORT=3334
# <!-- /SECTION: config -->

# <!-- SECTION: helpers -->
log_info() { echo "[INFO] $*"; }
log_warn() { echo "[WARN] $*"; }
log_error() { echo "[ERROR] $*" >&2; }
# <!-- /SECTION: helpers -->

# <!-- SECTION: hooks.pre_stop -->
# <!-- /SECTION: hooks.pre_stop -->

# <!-- SECTION: stop -->
log_info "Stopping edison-ui e2e servers"
log_info "  PROJECT_ROOT=$PROJECT_ROOT"
log_info "  MAIN_REPO_ROOT=$MAIN_REPO_ROOT"
log_info "  SESSION_ID=$SESSION_ID"

# Stop backend
log_info "Stopping backend (uvicorn on port $BACKEND_PORT)..."
pkill -f "uvicorn main:app.*--port $BACKEND_PORT" 2>/dev/null || true

# Stop frontend
log_info "Stopping frontend (next on port $FRONTEND_PORT)..."
pkill -f "next dev.*$FRONTEND_PORT" 2>/dev/null || true
pkill -f "next.*$FRONTEND_PORT" 2>/dev/null || true

# Give processes time to terminate
sleep 1

# Verify ports are free
if lsof -ti:"$BACKEND_PORT" >/dev/null 2>&1; then
  log_warn "Port $BACKEND_PORT still in use, force killing..."
  lsof -ti:"$BACKEND_PORT" | xargs kill -9 2>/dev/null || true
fi

if lsof -ti:"$FRONTEND_PORT" >/dev/null 2>&1; then
  log_warn "Port $FRONTEND_PORT still in use, force killing..."
  lsof -ti:"$FRONTEND_PORT" | xargs kill -9 2>/dev/null || true
fi

log_info "Servers stopped"
# <!-- /SECTION: stop -->

# <!-- SECTION: hooks.post_stop -->
# <!-- /SECTION: hooks.post_stop -->
