# Edison UI Backend

FastAPI backend for Edison UI, providing API access to Edison projects.

## Quick Start

```bash
# From project root
make install        # Install dependencies
make dev-backend    # Start backend server
```

## Configuration

Copy `.env.example` to `.env` and configure as needed:

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| **Project Discovery** |||
| `SCAN_ROOTS` | `~/projects` | Comma-separated directories to scan for Edison projects |
| `SCAN_IGNORE_PATTERNS` | `node_modules,.git,.venv,__pycache__` | Glob patterns to ignore during discovery |
| **Exposure Mode** |||
| `EXPOSURE_MODE` | `localhost` | `localhost` (127.0.0.1, no auth) or `exposed` (0.0.0.0, requires pairing) |
| **Realtime Updates** |||
| `REALTIME_ENABLED` | `true` | Enable WebSocket push updates |
| `REALTIME_WATCHER_ENABLED` | `true` | Enable filesystem watchers (falls back to polling) |
| `REALTIME_POLLING_INTERVAL_MS` | `5000` | Polling interval when watchers unavailable |
| **API** |||
| `API_HOST` | `127.0.0.1` | Server bind host |
| `API_PORT` | `8000` | Server port |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins |
| **Environment** |||
| `ENVIRONMENT` | `development` | `development` or `production` |
| `DEBUG` | `true` | Enable debug mode |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Exposure Modes

**localhost (default)**
- Binds to 127.0.0.1 only
- No authentication required
- Safe for local development

**exposed**
- Binds to 0.0.0.0 (network accessible)
- Requires pairing/authentication for remote clients
- Use for mobile access over LAN

## Development

### Run Tests

```bash
make backend-test
```

### Linting & Type Checking

```bash
make backend-lint     # ruff + mypy
make backend-format   # ruff format
```

## API Documentation

When running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
