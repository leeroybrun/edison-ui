#!/usr/bin/env bash
# Edison Web Server Verify Script for edison-ui
#
# Based on Edison core template: templates/scripts/web-server/verify-server.sh.template
#
# Verifies that the e2e servers are running from the correct worktree.
#
# Exit 0 if servers are correct for this worktree, non-zero otherwise.

set -euo pipefail

# <!-- SECTION: config -->
PROJECT_ROOT="${AGENTS_PROJECT_ROOT:-$(pwd)}"
MAIN_REPO_ROOT="${AGENTS_MAIN_REPO_ROOT:-$PROJECT_ROOT}"
SESSION_ID="${AGENTS_SESSION:-main}"

BACKEND_PORT=8002
FRONTEND_PORT=3334
BACKEND_PATTERN="uvicorn main:app.*--port $BACKEND_PORT"
# <!-- /SECTION: config -->

# <!-- SECTION: helpers -->
log_info() { echo "[INFO] $*"; }
log_ok() { echo "[OK] $*"; }
log_error() { echo "[ERROR] $*" >&2; }

verify_process_cwd() {
  local pattern="$1"
  local description="$2"

  local pid
  pid="$(pgrep -f "$pattern" 2>/dev/null | head -n 1 || true)"
  if [[ -z "$pid" ]]; then
    log_error "process_cwd ($description): no process matching '$pattern'"
    return 1
  fi

  # Linux: /proc
  if [[ -e "/proc/$pid/cwd" ]]; then
    local cwd_path
    cwd_path="$(readlink "/proc/$pid/cwd" 2>/dev/null || true)"
    if [[ -n "$cwd_path" && "$cwd_path" == "$PROJECT_ROOT"* ]]; then
      log_ok "process_cwd ($description): PID $pid is running from correct worktree"
      log_ok "  $cwd_path"
      return 0
    fi
    log_error "process_cwd ($description): PID $pid is running from wrong directory"
    log_error "  expected: $PROJECT_ROOT"
    log_error "  actual:   ${cwd_path:-<unknown>}"
    return 1
  fi

  # macOS: lsof
  local cwd_path
  cwd_path="$(lsof -p "$pid" 2>/dev/null | awk '$4=="cwd" {print $NF; exit}' || true)"
  if [[ -z "$cwd_path" ]]; then
    log_error "process_cwd ($description): could not determine cwd for pid=$pid"
    return 1
  fi
  if [[ "$cwd_path" == "$PROJECT_ROOT"* ]]; then
    log_ok "process_cwd ($description): PID $pid is running from correct worktree"
    log_ok "  $cwd_path"
    return 0
  fi
  log_error "process_cwd ($description): PID $pid is running from wrong directory"
  log_error "  expected: $PROJECT_ROOT"
  log_error "  actual:   $cwd_path"
  return 1
}

verify_port_process_cwd() {
  local port="$1"
  local description="$2"

  # Get PID listening on port
  local pid
  pid="$(lsof -ti:"$port" 2>/dev/null | head -n 1 || true)"
  if [[ -z "$pid" ]]; then
    log_error "port_cwd ($description): no process listening on port $port"
    return 1
  fi

  # macOS: lsof for cwd
  local cwd_path
  cwd_path="$(lsof -p "$pid" 2>/dev/null | awk '$4=="cwd" {print $NF; exit}' || true)"
  if [[ -z "$cwd_path" ]]; then
    log_error "port_cwd ($description): could not determine cwd for pid=$pid on port $port"
    return 1
  fi
  if [[ "$cwd_path" == "$PROJECT_ROOT"* ]]; then
    log_ok "port_cwd ($description): PID $pid on port $port is running from correct worktree"
    log_ok "  $cwd_path"
    return 0
  fi
  log_error "port_cwd ($description): PID $pid on port $port is running from wrong directory"
  log_error "  expected: $PROJECT_ROOT"
  log_error "  actual:   $cwd_path"
  return 1
}

verify_http() {
  local url="$1"
  local description="$2"

  if curl -sf "$url" >/dev/null 2>&1; then
    log_ok "http ($description): $url is responding"
    return 0
  fi
  log_error "http ($description): $url is not responding"
  return 1
}
# <!-- /SECTION: helpers -->

# <!-- SECTION: hooks.pre_verify -->
# <!-- /SECTION: hooks.pre_verify -->

# <!-- SECTION: verify -->
log_info "Verifying edison-ui e2e servers"
log_info "  PROJECT_ROOT=$PROJECT_ROOT"
log_info "  MAIN_REPO_ROOT=$MAIN_REPO_ROOT"
log_info "  SESSION_ID=$SESSION_ID"

errors=0

# Verify HTTP endpoints are responding
if ! verify_http "http://localhost:$FRONTEND_PORT" "frontend"; then
  ((errors++))
fi

if ! verify_http "http://localhost:$BACKEND_PORT/api/v1/health" "backend"; then
  ((errors++))
fi

# Verify processes are running from correct worktree
# Backend: use pattern match (uvicorn)
if ! verify_process_cwd "$BACKEND_PATTERN" "backend"; then
  ((errors++))
fi

# Frontend: use port-based check (Next.js production uses node/next-server)
if ! verify_port_process_cwd "$FRONTEND_PORT" "frontend"; then
  ((errors++))
fi

if [[ $errors -gt 0 ]]; then
  log_error "Verification failed with $errors error(s)"
  exit 1
fi

log_ok "All verification checks passed"
# <!-- /SECTION: verify -->

# <!-- SECTION: hooks.post_verify -->
# <!-- /SECTION: hooks.post_verify -->
