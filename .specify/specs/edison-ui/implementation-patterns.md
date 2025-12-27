# Edison UI - Implementation Patterns

This document provides code patterns and examples for implementing Edison UI. Reference these patterns when working on tasks.

## Backend Patterns

### Edison Service Wrapper Pattern
```python
# services/edison_service.py
from edison.core.session.lifecycle.manager import SessionManager
from edison.core.task.manager import TaskManager
from edison.core.qa.manager import QAManager
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class EdisonService:
    """Thin wrapper around Edison managers - NO business logic reimplementation"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        # Direct Edison manager usage
        self.session_manager = SessionManager()
        self.task_manager = TaskManager()
        self.qa_manager = QAManager()

    async def get_session(self, session_id: str) -> dict:
        """Get session with Edison's SessionManager"""
        try:
            # Set project context
            with edison_context(self.project_root):
                session = self.session_manager.get_session(session_id)
                if not session:
                    raise HTTPException(404, f"Session {session_id} not found")
                return session.to_dict()
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            raise HTTPException(500, detail=str(e))
```

### API Endpoint Pattern
```python
# api/routes/sessions.py
from fastapi import APIRouter, Depends, Query
from typing import Optional
from models.requests import CreateSessionRequest
from models.responses import SessionResponse, SessionListResponse

router = APIRouter(prefix="/api/v1/projects/{project_id}")

@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    project_id: str,
    state: Optional[str] = Query(None, regex="^(draft|active|done|validated)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    edison: EdisonService = Depends(get_edison_service)
):
    """List sessions with filtering and pagination"""
    # Input validation via Pydantic/FastAPI
    # Edison integration
    sessions = await edison.list_sessions(
        state=state,
        offset=(page - 1) * page_size,
        limit=page_size
    )

    # Transform to API response
    return SessionListResponse(
        items=[SessionResponse.from_edison(s) for s in sessions],
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=await edison.count_sessions(state=state)
        )
    )
```

### Input Validation Pattern
```python
# models/requests.py
from pydantic import BaseModel, Field, validator
import re
import bleach

class CreateTaskRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field("", max_length=10000)
    session_id: Optional[str] = Field(None, regex="^[a-z0-9-]+$")

    @validator('title')
    def sanitize_title(cls, v):
        # Remove any HTML/script tags
        clean = bleach.clean(v, tags=[], strip=True)
        # Remove leading/trailing whitespace
        clean = clean.strip()
        if not clean:
            raise ValueError("Title cannot be empty after sanitization")
        return clean

    @validator('session_id')
    def validate_session_id(cls, v):
        if v and len(v) > 50:
            raise ValueError("Session ID too long")
        return v
```

### Error Handling Pattern
```python
# core/exceptions.py
from fastapi import HTTPException
from fastapi.responses import JSONResponse

class EdisonUIError(Exception):
    def __init__(self, code: str, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}

@app.exception_handler(EdisonUIError)
async def edison_error_handler(request, exc: EdisonUIError):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "correlation_id": request.headers.get("X-Correlation-ID"),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )
```

### Testing Pattern (No Mocks!)
```python
# tests/integration/test_sessions.py
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

@pytest.fixture
def edison_project(tmp_path: Path):
    """Create a real Edison project for testing"""
    project = tmp_path / "test_project"
    project.mkdir()

    # Create Edison structure
    (project / ".edison").mkdir()
    (project / ".project" / "management").mkdir(parents=True)

    # Create test session
    session_file = project / ".project/management/sessions/draft/test-session/session.json"
    session_file.parent.mkdir(parents=True)
    session_file.write_text(json.dumps({
        "id": "test-session",
        "state": "draft",
        "created_at": datetime.utcnow().isoformat()
    }))

    return project

@pytest.mark.asyncio
async def test_get_session_with_real_edison(edison_project, client: TestClient):
    """Test with real Edison integration"""
    response = client.get(f"/api/v1/projects/{project_id}/sessions/test-session")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["id"] == "test-session"
    assert data["data"]["state"] == "draft"
```

## Frontend Patterns

### Component Structure Pattern
```tsx
// components/SessionCard.tsx
interface SessionCardProps {
  session: Session;
  onTransition?: (targetState: SessionState) => Promise<void>;
  isCompact?: boolean;
}

export function SessionCard({
  session,
  onTransition,
  isCompact = false
}: SessionCardProps) {
  // 1. Hooks at top
  const [isTransitioning, setIsTransitioning] = useState(false);
  const queryClient = useQueryClient();

  // 2. Derived state
  const canTransition = session.availableTransitions.length > 0;

  // 3. Handlers
  const handleTransition = useCallback(async (targetState: SessionState) => {
    setIsTransitioning(true);
    try {
      await onTransition?.(targetState);
      // Optimistic update
      queryClient.setQueryData(
        ['session', session.id],
        (old) => ({ ...old, state: targetState })
      );
    } catch (error) {
      toast.error('Transition failed');
    } finally {
      setIsTransitioning(false);
    }
  }, [onTransition, session.id]);

  // 4. Early returns
  if (!session) return null;

  // 5. Render
  return (
    <Card className={cn(
      "p-4",
      isCompact && "p-2",
      isTransitioning && "opacity-50"
    )}>
      {/* Component content */}
    </Card>
  );
}
```

### API Client Pattern
```typescript
// lib/api/client.ts
import axios, { AxiosInstance } from 'axios';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL,
      timeout: 30000,
    });

    // Request interceptor
    this.client.interceptors.request.use((config) => {
      const correlationId = crypto.randomUUID();
      config.headers['X-Correlation-ID'] = correlationId;
      return config;
    });

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.data?.error) {
          const apiError = error.response.data.error;
          console.error(`API Error ${apiError.code}: ${apiError.message}`);
        }
        return Promise.reject(error);
      }
    );
  }

  // Type-safe methods
  async getSessions(projectId: string): Promise<SessionListResponse> {
    const { data } = await this.client.get(`/projects/${projectId}/sessions`);
    return data;
  }
}

export const apiClient = new ApiClient();
```

### State Management Pattern
```typescript
// stores/uiStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UIState {
  // State
  sidebarOpen: boolean;
  selectedProjectId: string | null;
  pinnedProjects: string[];
  theme: 'light' | 'dark';

  // Actions
  toggleSidebar: () => void;
  selectProject: (id: string | null) => void;
  togglePinProject: (id: string) => void;
  setTheme: (theme: 'light' | 'dark') => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      // Initial state
      sidebarOpen: true,
      selectedProjectId: null,
      pinnedProjects: [],
      theme: 'light',

      // Actions
      toggleSidebar: () => set((state) => ({
        sidebarOpen: !state.sidebarOpen
      })),

      selectProject: (id) => set({
        selectedProjectId: id
      }),

      togglePinProject: (id) => set((state) => ({
        pinnedProjects: state.pinnedProjects.includes(id)
          ? state.pinnedProjects.filter(p => p !== id)
          : [...state.pinnedProjects, id]
      })),

      setTheme: (theme) => set({ theme }),
    }),
    {
      name: 'edison-ui-store',
      partialize: (state) => ({
        pinnedProjects: state.pinnedProjects,
        theme: state.theme,
      }),
    }
  )
);
```

### WebSocket Hook Pattern
```typescript
// hooks/useWebSocket.ts
export function useWebSocket(projectId: string) {
  const [isConnected, setIsConnected] = useState(false);
  const queryClient = useQueryClient();
  const reconnectAttempts = useRef(0);

  useEffect(() => {
    const ws = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL}/ws`);

    ws.onopen = () => {
      setIsConnected(true);
      reconnectAttempts.current = 0;

      // Subscribe to project
      ws.send(JSON.stringify({
        type: 'subscribe',
        channels: [`project:${projectId}`, 'task:*', 'session:*'],
        correlationId: crypto.randomUUID(),
      }));
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      switch (message.type) {
        case 'entity:update':
          // Update cache
          queryClient.setQueryData(
            [message.entity.type, message.entity.id],
            message.entity.data
          );
          break;

        case 'file:change':
          // Invalidate affected queries
          queryClient.invalidateQueries([message.entityType]);
          break;
      }
    };

    ws.onclose = () => {
      setIsConnected(false);

      // Exponential backoff reconnect
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
      reconnectAttempts.current++;

      setTimeout(() => {
        if (document.visibilityState === 'visible') {
          // Reconnect
        }
      }, delay);
    };

    return () => ws.close();
  }, [projectId]);

  return { isConnected };
}
```

### Testing Pattern
```tsx
// components/__tests__/SessionCard.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SessionCard } from '../SessionCard';

describe('SessionCard', () => {
  const mockSession = {
    id: 'test-session',
    state: 'draft' as const,
    availableTransitions: ['active'],
    owner: 'test-user',
  };

  it('displays session information', () => {
    render(<SessionCard session={mockSession} />);

    expect(screen.getByText('test-session')).toBeInTheDocument();
    expect(screen.getByText('draft')).toBeInTheDocument();
  });

  it('handles state transition', async () => {
    const onTransition = jest.fn().mockResolvedValue(void 0);
    const user = userEvent.setup();

    render(
      <SessionCard
        session={mockSession}
        onTransition={onTransition}
      />
    );

    const transitionButton = screen.getByRole('button', {
      name: /transition to active/i
    });
    await user.click(transitionButton);

    expect(onTransition).toHaveBeenCalledWith('active');
  });

  it('shows loading state during transition', async () => {
    const onTransition = jest.fn(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );
    const user = userEvent.setup();

    render(
      <SessionCard
        session={mockSession}
        onTransition={onTransition}
      />
    );

    const button = screen.getByRole('button', {
      name: /transition/i
    });
    await user.click(button);

    expect(button).toBeDisabled();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });
});
```

## Common Patterns

### File Path Parsing
```python
def parse_edison_path(file_path: str) -> tuple[str, str]:
    """Extract entity type and ID from Edison file path"""
    # Example: .project/management/tasks/todo/TASK-001.md
    # Returns: ('task', 'TASK-001')

    path_parts = Path(file_path).parts

    if 'tasks' in path_parts:
        entity_type = 'task'
        # Extract ID from filename
        entity_id = Path(file_path).stem
    elif 'sessions' in path_parts:
        entity_type = 'session'
        # Session ID is directory name
        entity_id = path_parts[-2]
    elif 'qa' in path_parts:
        entity_type = 'qa'
        entity_id = path_parts[-3]  # task ID
    else:
        return None, None

    return entity_type, entity_id
```

### Project ID Generation
```python
import hashlib

def generate_project_id(project_path: str) -> str:
    """Generate stable project ID from absolute path"""
    abs_path = Path(project_path).absolute()
    path_bytes = str(abs_path).encode('utf-8')
    return hashlib.sha256(path_bytes).hexdigest()[:16]
```

### Debouncing File Events
```python
from collections import defaultdict
from datetime import datetime, timedelta

class FileEventDebouncer:
    def __init__(self, window_ms: int = 100):
        self.window = timedelta(milliseconds=window_ms)
        self.pending = defaultdict(lambda: None)

    def should_process(self, file_path: str) -> bool:
        now = datetime.utcnow()
        last_event = self.pending[file_path]

        if last_event is None or (now - last_event) > self.window:
            self.pending[file_path] = now
            return True

        return False
```

---

*Reference these patterns when implementing Edison UI tasks. Always prefer Edison's native functionality over reimplementation.*