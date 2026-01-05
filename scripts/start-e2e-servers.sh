#!/bin/bash
# Start backend and frontend servers for browser-e2e validation

set -e

# Configuration
BACKEND_PORT=8002
FRONTEND_PORT=3334
SCAN_ROOTS="/Users/leeroy/Documents/Development"

# Resolve the project root (parent of scripts directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Script directory: $SCRIPT_DIR"
echo "Project root: $PROJECT_ROOT"

# Kill any existing processes on our ports
pkill -f "uvicorn main:app.*--port $BACKEND_PORT" 2>/dev/null || true
pkill -f "next dev.*$FRONTEND_PORT" 2>/dev/null || true
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

# Start backend in background
echo "Starting backend on port $BACKEND_PORT..."
cd "$PROJECT_ROOT/backend"
source .venv/bin/activate
SCAN_ROOTS="$SCAN_ROOTS" \
API_PORT="$BACKEND_PORT" \
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

# Start frontend in foreground (this keeps the script running)
echo "Starting frontend on port $FRONTEND_PORT..."
cd "$PROJECT_ROOT/frontend"
NEXT_PUBLIC_API_URL="http://localhost:$BACKEND_PORT" pnpm dev -p "$FRONTEND_PORT"
