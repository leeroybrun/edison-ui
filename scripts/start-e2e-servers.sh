#!/bin/bash
# Start backend and frontend servers for browser-e2e validation

set -e

# Configuration
BACKEND_PORT=8002
FRONTEND_PORT=3334
SCAN_ROOTS="/Users/leeroy/Documents/Development"

# Resolve the project root (prefer Edison-injected AGENTS_PROJECT_ROOT)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${AGENTS_PROJECT_ROOT:-$(dirname "$SCRIPT_DIR")}"

echo "Script directory: $SCRIPT_DIR"
echo "Project root: $PROJECT_ROOT (AGENTS_PROJECT_ROOT=${AGENTS_PROJECT_ROOT:-<not set>})"

# Kill any existing processes on our ports
pkill -f "uvicorn main:app.*--port $BACKEND_PORT" 2>/dev/null || true
pkill -f "next.*$FRONTEND_PORT" 2>/dev/null || true
lsof -ti:$BACKEND_PORT | xargs -r kill 2>/dev/null || true
lsof -ti:$FRONTEND_PORT | xargs -r kill 2>/dev/null || true
sleep 1

# Check if backend and frontend directories exist
if [[ ! -d "$PROJECT_ROOT/backend" ]]; then
    echo "ERROR: Backend directory not found at $PROJECT_ROOT/backend"
    exit 1
fi

if [[ ! -d "$PROJECT_ROOT/frontend" ]]; then
    echo "ERROR: Frontend directory not found at $PROJECT_ROOT/frontend"
    exit 1
fi

# Create test-specific settings directory and file with localhost mode
# This ensures e2e tests don't require authentication
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
echo "Created test settings at $TEST_SETTINGS_FILE with exposureMode=localhost"

# Start backend in background with test settings
echo "Starting backend on port $BACKEND_PORT..."
cd "$PROJECT_ROOT/backend"
source .venv/bin/activate
SETTINGS_FILE="$TEST_SETTINGS_FILE" \
PAIRING_FILE="$TEST_PAIRING_FILE" \
SCAN_ROOTS="$SCAN_ROOTS" \
API_PORT="$BACKEND_PORT" \
FRONTEND_PORT="$FRONTEND_PORT" \
CORS_ORIGINS='["http://localhost:'"$FRONTEND_PORT"'","http://localhost:3000"]' \
python -m uvicorn main:app --host 127.0.0.1 --port "$BACKEND_PORT" &

BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend on port $BACKEND_PORT..."
for i in {1..30}; do
    if curl -s "http://localhost:$BACKEND_PORT/api/v1/health" > /dev/null 2>&1; then
        echo "Backend ready!"
        break
    fi
    if ! ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "ERROR: Backend process died"
        exit 1
    fi
    sleep 1
done

# Verify backend is actually running
if ! curl -s "http://localhost:$BACKEND_PORT/api/v1/health" > /dev/null 2>&1; then
    echo "ERROR: Backend failed to start"
    exit 1
fi

# Build and start frontend in production mode for stable asset serving
# Dev mode has EMFILE and chunk-serving issues during long validation runs
echo "Building frontend..."
cd "$PROJECT_ROOT/frontend"
NEXT_PUBLIC_API_URL="http://localhost:$BACKEND_PORT" pnpm build

echo "Starting frontend on port $FRONTEND_PORT in production mode..."
NEXT_PUBLIC_API_URL="http://localhost:$BACKEND_PORT" pnpm start -p "$FRONTEND_PORT"
