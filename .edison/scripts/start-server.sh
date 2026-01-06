#!/usr/bin/env bash
# Edison Web Server Start Script for edison-ui
#
# Based on Edison core template: templates/scripts/web-server/start-server.sh.template
#
# Starts the e2e test stack: FastAPI backend (port 8002) + Next.js frontend (port 3334)
#
# Worktree awareness:
# - Uses `AGENTS_PROJECT_ROOT` (injected by Edison) as the source of truth

set -euo pipefail

# <!-- SECTION: config -->
PROJECT_ROOT="${AGENTS_PROJECT_ROOT:-$(pwd)}"
MAIN_REPO_ROOT="${AGENTS_MAIN_REPO_ROOT:-$PROJECT_ROOT}"
SESSION_ID="${AGENTS_SESSION:-main}"

BACKEND_PORT=8002
FRONTEND_PORT=3334
SCAN_ROOTS="/Users/leeroy/Documents/Development"
# <!-- /SECTION: config -->

# <!-- SECTION: helpers -->
log_info() { echo "[INFO] $*"; }
log_warn() { echo "[WARN] $*"; }
log_error() { echo "[ERROR] $*" >&2; }

wait_for_health() {
  local url=$1
  local max_wait=${2:-60}
  local waited=0
  while ! curl -sf "$url" >/dev/null 2>&1; do
    if [ "$waited" -ge "$max_wait" ]; then
      log_error "Timeout waiting for $url after ${max_wait}s"
      return 1
    fi
    sleep 1
    waited=$((waited + 1))
  done
  log_info "$url ready after ${waited}s"
  return 0
}
# <!-- /SECTION: helpers -->

# <!-- SECTION: hooks.pre_start -->
# Kill any existing processes on our ports
pkill -f "uvicorn main:app.*--port $BACKEND_PORT" 2>/dev/null || true
pkill -f "next.*$FRONTEND_PORT" 2>/dev/null || true
lsof -ti:"$BACKEND_PORT" 2>/dev/null | xargs kill 2>/dev/null || true
lsof -ti:"$FRONTEND_PORT" 2>/dev/null | xargs kill 2>/dev/null || true
sleep 1
# <!-- /SECTION: hooks.pre_start -->

# <!-- SECTION: start -->
log_info "Starting edison-ui e2e servers"
log_info "  PROJECT_ROOT=$PROJECT_ROOT"
log_info "  MAIN_REPO_ROOT=$MAIN_REPO_ROOT"
log_info "  SESSION_ID=$SESSION_ID"

cd "$PROJECT_ROOT"

# Verify directories exist
if [[ ! -d "$PROJECT_ROOT/backend" ]]; then
  log_error "Backend directory not found at $PROJECT_ROOT/backend"
  exit 1
fi

if [[ ! -d "$PROJECT_ROOT/frontend" ]]; then
  log_error "Frontend directory not found at $PROJECT_ROOT/frontend"
  exit 1
fi

# Create test settings for e2e with localhost mode (no auth required)
TEST_SETTINGS_DIR="/tmp/edison-ui-e2e-test"
TEST_SETTINGS_FILE="$TEST_SETTINGS_DIR/settings.json"
TEST_PAIRING_FILE="$TEST_SETTINGS_DIR/pairing.json"
mkdir -p "$TEST_SETTINGS_DIR"
cat > "$TEST_SETTINGS_FILE" << 'EOF'
{
  "scanRoots": ["/Users/leeroy/Documents/Development"],
  "displayName": "E2E Test User",
  "firstRunComplete": true,
  "exposureMode": "localhost",
  "realtimeEnabled": true,
  "realtimeWatcherEnabled": true,
  "realtimePollingIntervalMs": 5000
}
EOF
log_info "Created test settings at $TEST_SETTINGS_FILE with exposureMode=localhost"

# Start backend
log_info "Starting backend on port $BACKEND_PORT..."
cd "$PROJECT_ROOT/backend"

# Activate venv if it exists
if [[ -f ".venv/bin/activate" ]]; then
  source .venv/bin/activate
  log_info "Activated backend venv"
fi

SETTINGS_FILE="$TEST_SETTINGS_FILE" \
PAIRING_FILE="$TEST_PAIRING_FILE" \
SCAN_ROOTS="$SCAN_ROOTS" \
API_PORT="$BACKEND_PORT" \
FRONTEND_PORT="$FRONTEND_PORT" \
CORS_ORIGINS='["http://localhost:'"$FRONTEND_PORT"'","http://localhost:3000"]' \
nohup python -m uvicorn main:app --host 127.0.0.1 --port "$BACKEND_PORT" \
  > /tmp/edison-ui-backend.log 2>&1 &

BACKEND_PID=$!
log_info "Backend started with PID $BACKEND_PID"

log_info "Waiting for backend health endpoint..."
if ! wait_for_health "http://localhost:$BACKEND_PORT/api/v1/health" 60; then
  log_error "Backend failed to start. Check /tmp/edison-ui-backend.log"
  cat /tmp/edison-ui-backend.log
  exit 1
fi

# Build and start frontend in production mode (more stable than dev mode)
log_info "Building frontend..."
cd "$PROJECT_ROOT/frontend"
NEXT_PUBLIC_API_URL="http://localhost:$BACKEND_PORT" pnpm build

log_info "Starting frontend on port $FRONTEND_PORT in production mode..."
NEXT_PUBLIC_API_URL="http://localhost:$BACKEND_PORT" nohup pnpm start -p "$FRONTEND_PORT" \
  > /tmp/edison-ui-frontend.log 2>&1 &

FRONTEND_PID=$!
log_info "Frontend started with PID $FRONTEND_PID"

log_info "Waiting for frontend..."
if ! wait_for_health "http://localhost:$FRONTEND_PORT" 120; then
  log_error "Frontend failed to start. Check /tmp/edison-ui-frontend.log"
  cat /tmp/edison-ui-frontend.log
  exit 1
fi

log_info "Both servers started successfully"
log_info "  Backend:  http://localhost:$BACKEND_PORT"
log_info "  Frontend: http://localhost:$FRONTEND_PORT"
# <!-- /SECTION: start -->

# <!-- SECTION: hooks.post_start -->
# Final verification
if curl -sf "http://localhost:$BACKEND_PORT/api/v1/health" >/dev/null 2>&1; then
  log_info "Backend health check passed"
else
  log_warn "Backend health check not responding"
fi

if curl -sf "http://localhost:$FRONTEND_PORT" >/dev/null 2>&1; then
  log_info "Frontend responding"
else
  log_warn "Frontend not yet responding (may still be starting)"
fi
# <!-- /SECTION: hooks.post_start -->
