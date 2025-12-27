# Edison UI - Data Models and Contracts

## Overview
This document defines all data models, API contracts, and interfaces for Edison UI. All models are strongly typed using Pydantic (backend) and TypeScript (frontend).

## Core Domain Models

### Project Model
```python
# backend/models/domain/project.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict

class ProjectMetadata(BaseModel):
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    owner: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    config_version: str = "1.0.0"

class ProjectStats(BaseModel):
    total_tasks: int = 0
    active_sessions: int = 0
    pending_tasks: int = 0
    validation_rate: float = 0.0
    last_activity: Optional[datetime] = None

class Project(BaseModel):
    id: str  # Path-based ID (hashed)
    path: str  # Absolute file path
    metadata: ProjectMetadata
    stats: ProjectStats
    has_git: bool = False
    git_branch: Optional[str] = None
    is_healthy: bool = True
    errors: List[str] = Field(default_factory=list)
```

```typescript
// frontend/types/models/project.ts
export interface ProjectMetadata {
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
  owner?: string;
  tags: string[];
  configVersion: string;
}

export interface ProjectStats {
  totalTasks: number;
  activeSessions: number;
  pendingTasks: number;
  validationRate: number;
  lastActivity?: string;
}

export interface Project {
  id: string;
  path: string;
  metadata: ProjectMetadata;
  stats: ProjectStats;
  hasGit: boolean;
  gitBranch?: string;
  isHealthy: boolean;
  errors: string[];
}
```

### Session Model
```python
# backend/models/domain/session.py
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

class SessionState(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    BLOCKED = "blocked"
    DONE = "done"
    CLOSING = "closing"
    VALIDATED = "validated"
    RECOVERY = "recovery"
    ARCHIVED = "archived"

class GitInfo(BaseModel):
    branch: str
    worktree_path: str
    base_branch: Optional[str] = None
    commits_ahead: int = 0
    commits_behind: int = 0
    has_changes: bool = False

class StateTransition(BaseModel):
    from_state: SessionState
    to_state: SessionState
    timestamp: datetime
    reason: Optional[str] = None
    triggered_by: str = "user"
    guards_passed: List[str] = Field(default_factory=list)
    conditions_met: List[str] = Field(default_factory=list)

class Session(BaseModel):
    id: str
    state: SessionState
    project_id: str
    owner: str
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    git_info: Optional[GitInfo] = None
    activity_log: List[Dict[str, Any]] = Field(default_factory=list)
    state_history: List[StateTransition] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    task_ids: List[str] = Field(default_factory=list)  # Lightweight index
    timeout_at: Optional[datetime] = None
    recovery_available: bool = False
```

```typescript
// frontend/types/models/session.ts
export enum SessionState {
  DRAFT = "draft",
  ACTIVE = "active",
  BLOCKED = "blocked",
  DONE = "done",
  CLOSING = "closing",
  VALIDATED = "validated",
  RECOVERY = "recovery",
  ARCHIVED = "archived"
}

export interface GitInfo {
  branch: string;
  worktreePath: string;
  baseBranch?: string;
  commitsAhead: number;
  commitsBehind: number;
  hasChanges: boolean;
}

export interface StateTransition {
  fromState: SessionState;
  toState: SessionState;
  timestamp: string;
  reason?: string;
  triggeredBy: string;
  guardsPassed: string[];
  conditionsMet: string[];
}

export interface Session {
  id: string;
  state: SessionState;
  projectId: string;
  owner: string;
  createdAt: string;
  updatedAt: string;
  closedAt?: string;
  gitInfo?: GitInfo;
  activityLog: Array<Record<string, any>>;
  stateHistory: StateTransition[];
  metadata: Record<string, any>;
  taskIds: string[];
  timeoutAt?: string;
  recoveryAvailable: boolean;
}
```

### Task Model
```python
# backend/models/domain/task.py
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

class TaskState(str, Enum):
    TODO = "todo"
    WIP = "wip"
    BLOCKED = "blocked"
    DONE = "done"
    VALIDATED = "validated"

class TaskMetadata(BaseModel):
    created_at: datetime
    updated_at: datetime
    claimed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    validated_at: Optional[datetime] = None
    time_estimate: Optional[int] = None  # minutes
    time_spent: Optional[int] = None  # minutes

class DelegationInfo(BaseModel):
    agent: str
    delegated_at: datetime
    model: Optional[str] = None
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None

class Task(BaseModel):
    id: str
    state: TaskState
    title: str
    description: str  # Markdown content
    session_id: Optional[str] = None
    owner: Optional[str] = None
    parent_id: Optional[str] = None
    child_ids: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    metadata: TaskMetadata
    delegation: Optional[DelegationInfo] = None
    qa_id: Optional[str] = None
    state_history: List[Dict[str, Any]] = Field(default_factory=list)
    priority: int = 0  # 0=normal, 1=high, 2=urgent
    blocked_by: List[str] = Field(default_factory=list)
    blocks: List[str] = Field(default_factory=list)
```

```typescript
// frontend/types/models/task.ts
export enum TaskState {
  TODO = "todo",
  WIP = "wip",
  BLOCKED = "blocked",
  DONE = "done",
  VALIDATED = "validated"
}

export interface TaskMetadata {
  createdAt: string;
  updatedAt: string;
  claimedAt?: string;
  completedAt?: string;
  validatedAt?: string;
  timeEstimate?: number;
  timeSpent?: number;
}

export interface DelegationInfo {
  agent: string;
  delegatedAt: string;
  model?: string;
  status: string;
  result?: Record<string, any>;
}

export interface Task {
  id: string;
  state: TaskState;
  title: string;
  description: string;
  sessionId?: string;
  owner?: string;
  parentId?: string;
  childIds: string[];
  tags: string[];
  metadata: TaskMetadata;
  delegation?: DelegationInfo;
  qaId?: string;
  stateHistory: Array<Record<string, any>>;
  priority: number;
  blockedBy: string[];
  blocks: string[];
}
```

### QA Model
```python
# backend/models/domain/qa.py
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

class QAState(str, Enum):
    WAITING = "waiting"
    TODO = "todo"
    WIP = "wip"
    DONE = "done"
    VALIDATED = "validated"

class ValidatorResult(BaseModel):
    validator_name: str
    engine: str
    status: str  # pass, fail, warning
    score: Optional[float] = None
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    executed_at: datetime
    duration_ms: int
    error: Optional[str] = None

class ValidationRound(BaseModel):
    round_number: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    validators: List[ValidatorResult] = Field(default_factory=list)
    bundle_report: Optional[Dict[str, Any]] = None
    evidence_path: str
    consensus: Optional[str] = None  # pass, fail, mixed

class QARecord(BaseModel):
    id: str  # Same as task_id
    task_id: str
    state: QAState
    created_at: datetime
    updated_at: datetime
    rounds: List[ValidationRound] = Field(default_factory=list)
    current_round: int = 0
    total_validators_run: int = 0
    pass_rate: float = 0.0
    requires_revalidation: bool = False
    revalidation_reason: Optional[str] = None
    implementation_phase: Optional[str] = None  # red, green, refactor
```

```typescript
// frontend/types/models/qa.ts
export enum QAState {
  WAITING = "waiting",
  TODO = "todo",
  WIP = "wip",
  DONE = "done",
  VALIDATED = "validated"
}

export interface ValidatorResult {
  validatorName: string;
  engine: string;
  status: "pass" | "fail" | "warning";
  score?: number;
  findings: Array<Record<string, any>>;
  executedAt: string;
  durationMs: number;
  error?: string;
}

export interface ValidationRound {
  roundNumber: number;
  startedAt: string;
  completedAt?: string;
  validators: ValidatorResult[];
  bundleReport?: Record<string, any>;
  evidencePath: string;
  consensus?: "pass" | "fail" | "mixed";
}

export interface QARecord {
  id: string;
  taskId: string;
  state: QAState;
  createdAt: string;
  updatedAt: string;
  rounds: ValidationRound[];
  currentRound: number;
  totalValidatorsRun: number;
  passRate: number;
  requiresRevalidation: boolean;
  revalidationReason?: string;
  implementationPhase?: "red" | "green" | "refactor";
}
```

## Configuration Models

### Edison Configuration
```python
# backend/models/domain/config.py
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional

class PackConfig(BaseModel):
    name: str
    enabled: bool
    version: str
    path: str
    dependencies: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)

class WorkflowConfig(BaseModel):
    states: List[str]
    transitions: Dict[str, List[Dict[str, Any]]]
    guards: Dict[str, Any]
    conditions: Dict[str, Any]
    actions: Dict[str, Any]

class EdisonConfig(BaseModel):
    project_name: str
    project_description: Optional[str] = None
    packs: List[PackConfig] = Field(default_factory=list)
    workflow: WorkflowConfig
    validators: Dict[str, Any] = Field(default_factory=dict)
    agents: Dict[str, Any] = Field(default_factory=dict)
    rules: Dict[str, Any] = Field(default_factory=dict)
    environment: Dict[str, str] = Field(default_factory=dict)
```

## API Contracts

### Request/Response Models

#### Project Endpoints
```python
# backend/models/api/project.py
from pydantic import BaseModel, Field
from typing import List, Optional

class ProjectScanRequest(BaseModel):
    paths: List[str] = Field(default_factory=list)
    max_depth: int = 5
    exclude_patterns: List[str] = Field(default_factory=list)

class ProjectListRequest(BaseModel):
    page: int = 1
    page_size: int = 25
    search: Optional[str] = None
    filter_healthy: Optional[bool] = None
    sort_by: str = "updated_at"
    sort_order: str = "desc"

class ProjectResponse(BaseModel):
    project: Project
    success: bool = True
    error: Optional[str] = None

class ProjectListResponse(BaseModel):
    projects: List[Project]
    total: int
    page: int
    page_size: int
    success: bool = True
```

#### Session Endpoints
```python
# backend/models/api/session.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class CreateSessionRequest(BaseModel):
    session_id: Optional[str] = None  # Auto-generate if not provided
    project_id: str
    owner: str
    mode: str = "normal"
    install_deps: bool = True
    base_branch: Optional[str] = None

class TransitionSessionRequest(BaseModel):
    target_state: SessionState
    reason: Optional[str] = None
    force: bool = False  # Bypass soft guards

class SessionResponse(BaseModel):
    session: Session
    available_transitions: List[str] = Field(default_factory=list)
    guards: Dict[str, bool] = Field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None

class SessionListResponse(BaseModel):
    sessions: List[Session]
    total: int
    filters_applied: Dict[str, Any]
    success: bool = True
```

#### Task Endpoints
```python
# backend/models/api/task.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class CreateTaskRequest(BaseModel):
    task_id: Optional[str] = None  # Auto-generate if not provided
    title: str
    description: str
    session_id: Optional[str] = None
    owner: Optional[str] = None
    parent_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    create_qa: bool = True

class UpdateTaskRequest(BaseModel):
    state: Optional[TaskState] = None
    title: Optional[str] = None
    description: Optional[str] = None
    owner: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: Optional[int] = None

class ClaimTaskRequest(BaseModel):
    session_id: str
    owner: str

class DelegateTaskRequest(BaseModel):
    agent: str
    model: Optional[str] = None

class TaskResponse(BaseModel):
    task: Task
    can_transition_to: List[TaskState]
    validation_status: Optional[str] = None
    success: bool = True
    error: Optional[str] = None

class TaskListResponse(BaseModel):
    tasks: List[Task]
    total: int
    by_state: Dict[str, int]
    success: bool = True
```

#### QA Endpoints
```python
# backend/models/api/qa.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class CreateRoundRequest(BaseModel):
    validators: Optional[List[str]] = None  # None = use defaults
    force_new: bool = False

class ValidateRequest(BaseModel):
    round_number: Optional[int] = None  # None = latest
    validators: List[str]
    parallel: bool = True
    timeout_seconds: int = 300

class QAResponse(BaseModel):
    qa_record: QARecord
    latest_round: Optional[ValidationRound] = None
    can_revalidate: bool
    success: bool = True
    error: Optional[str] = None

class ValidationReportResponse(BaseModel):
    report_type: str  # bundle, implementation, validator
    round_number: int
    content: Dict[str, Any]
    success: bool = True
```

### WebSocket Events

#### Event Contracts
```typescript
// frontend/types/websocket.ts
export interface WSMessage<T = any> {
  event: string;
  data: T;
  timestamp: string;
  correlationId?: string;
}

export interface WSSubscription {
  type: "project" | "session" | "task" | "qa";
  id: string;
}

export interface WSStateChange {
  entityType: string;
  entityId: string;
  oldState: string;
  newState: string;
  triggeredBy: string;
}

export interface WSFileChange {
  path: string;
  changeType: "created" | "modified" | "deleted";
  entityType?: string;
  entityId?: string;
}

export interface WSProgress {
  operationId: string;
  operation: string;
  progress: number;  // 0-100
  message: string;
  isComplete: boolean;
}

// Event names
export const WS_EVENTS = {
  // Client → Server
  SUBSCRIBE: "subscribe",
  UNSUBSCRIBE: "unsubscribe",
  PING: "ping",

  // Server → Client
  PROJECT_UPDATED: "project:updated",
  SESSION_TRANSITION: "session:transition",
  TASK_STATE_CHANGE: "task:stateChange",
  QA_ROUND_COMPLETE: "qa:roundComplete",
  FILE_CHANGED: "file:changed",
  PROGRESS_UPDATE: "progress:update",
  ERROR: "error",
  PONG: "pong"
} as const;
```

## Database Schemas

### UI Database (SQLite)
```sql
-- User preferences table
CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL UNIQUE,
    theme TEXT DEFAULT 'light',
    layout_config JSON,
    keyboard_shortcuts JSON,
    notification_preferences JSON,
    saved_filters JSON,
    favorite_projects JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- UI state persistence
CREATE TABLE ui_state (
    key TEXT PRIMARY KEY,
    value JSON NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytics events
CREATE TABLE analytics_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    event_category TEXT NOT NULL,
    event_data JSON,
    user_id TEXT,
    session_id TEXT,
    project_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at)
);

-- Search history
CREATE TABLE search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    search_type TEXT,
    filters JSON,
    results_count INTEGER,
    selected_result TEXT,
    user_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_query (user_id, query)
);

-- Saved searches
CREATE TABLE saved_searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    query TEXT NOT NULL,
    filters JSON,
    search_type TEXT,
    user_id TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name)
);

-- Notification queue
CREATE TABLE notification_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT,
    data JSON,
    user_id TEXT,
    read BOOLEAN DEFAULT FALSE,
    action_taken TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP,
    INDEX idx_user_unread (user_id, read)
);

-- Performance metrics
CREATE TABLE performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metric_unit TEXT,
    context JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_metric_time (metric_name, created_at)
);
```

## Cache Structures

### Redis Cache Keys
```python
# backend/services/cache_keys.py
from typing import Optional

class CacheKeys:
    """Standardized cache key patterns"""

    # Project cache
    PROJECT_LIST = "projects:list:{page}:{filters_hash}"
    PROJECT_DETAIL = "projects:detail:{project_id}"
    PROJECT_STATS = "projects:stats:{project_id}"
    PROJECT_SCAN = "projects:scan:{path_hash}"

    # Session cache
    SESSION_LIST = "sessions:list:{project_id}:{state}"
    SESSION_DETAIL = "sessions:detail:{session_id}"
    SESSION_TRANSITIONS = "sessions:transitions:{session_id}"

    # Task cache
    TASK_LIST = "tasks:list:{session_id}:{state}"
    TASK_DETAIL = "tasks:detail:{task_id}"
    TASK_BOARD = "tasks:board:{project_id}"

    # QA cache
    QA_DETAIL = "qa:detail:{task_id}"
    QA_ROUND = "qa:round:{task_id}:{round_num}"
    QA_REPORT = "qa:report:{task_id}:{report_type}"

    # Search cache
    SEARCH_RESULTS = "search:results:{query_hash}"
    SEARCH_SUGGESTIONS = "search:suggestions:{prefix}"

    # Analytics cache
    ANALYTICS_DAILY = "analytics:daily:{project_id}:{date}"
    ANALYTICS_METRICS = "analytics:metrics:{metric_type}:{period}"

    # Config cache
    CONFIG_PROJECT = "config:project:{project_id}"
    CONFIG_PACKS = "config:packs:{project_id}"
    CONFIG_SCHEMA = "config:schema:{schema_name}"

    @staticmethod
    def get_ttl(key_pattern: str) -> int:
        """Get TTL in seconds for cache key pattern"""
        ttl_map = {
            "projects:list": 300,      # 5 minutes
            "projects:detail": 600,    # 10 minutes
            "projects:stats": 120,     # 2 minutes
            "sessions:": 60,           # 1 minute (active changes)
            "tasks:": 120,             # 2 minutes
            "qa:": 180,                # 3 minutes
            "search:results": 600,     # 10 minutes
            "search:suggestions": 1800, # 30 minutes
            "analytics:daily": 3600,   # 1 hour
            "analytics:metrics": 900,  # 15 minutes
            "config:": 1800,           # 30 minutes
        }

        for prefix, ttl in ttl_map.items():
            if key_pattern.startswith(prefix):
                return ttl
        return 300  # Default 5 minutes
```

## Error Contracts

### Error Response Format
```python
# backend/models/api/errors.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class ErrorDetail(BaseModel):
    code: str  # Machine-readable error code
    message: str  # Human-readable message
    field: Optional[str] = None  # Field that caused error
    context: Dict[str, Any] = Field(default_factory=dict)

class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
    traceback: Optional[str] = None  # Only in debug mode
    correlation_id: str
    timestamp: str
    suggestions: List[str] = Field(default_factory=list)  # Help text

# Standard error codes
ERROR_CODES = {
    # Client errors (4xx)
    "VALIDATION_ERROR": "Invalid input data",
    "NOT_FOUND": "Resource not found",
    "UNAUTHORIZED": "Authentication required",
    "FORBIDDEN": "Permission denied",
    "CONFLICT": "Resource conflict",
    "RATE_LIMITED": "Too many requests",

    # Edison errors
    "EDISON_ERROR": "Edison operation failed",
    "STATE_TRANSITION_ERROR": "Invalid state transition",
    "GUARD_FAILED": "State guard check failed",
    "FILE_ACCESS_ERROR": "Cannot access Edison files",

    # Server errors (5xx)
    "INTERNAL_ERROR": "Internal server error",
    "SERVICE_UNAVAILABLE": "Service temporarily unavailable",
    "TIMEOUT": "Operation timed out",
}
```

## Validation Schemas

### JSON Schema for Configuration
```json
// schemas/edison-config.schema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Edison Configuration",
  "type": "object",
  "required": ["project", "workflow"],
  "properties": {
    "project": {
      "type": "object",
      "required": ["name"],
      "properties": {
        "name": { "type": "string" },
        "description": { "type": "string" }
      }
    },
    "workflow": {
      "type": "object",
      "required": ["states", "transitions"],
      "properties": {
        "states": {
          "type": "array",
          "items": { "type": "string" }
        },
        "transitions": {
          "type": "object",
          "additionalProperties": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["to"],
              "properties": {
                "to": { "type": "string" },
                "guards": { "type": "array" },
                "conditions": { "type": "array" },
                "actions": { "type": "array" }
              }
            }
          }
        }
      }
    },
    "packs": {
      "type": "object",
      "properties": {
        "active": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    },
    "validators": {
      "type": "object"
    },
    "agents": {
      "type": "object"
    }
  }
}
```

## Type Guards and Utilities

### TypeScript Type Guards
```typescript
// frontend/lib/typeGuards.ts
import { Session, Task, QARecord } from '@/types/models';

export function isSession(obj: any): obj is Session {
  return obj && typeof obj.id === 'string' && obj.state in SessionState;
}

export function isTask(obj: any): obj is Task {
  return obj && typeof obj.id === 'string' && obj.state in TaskState;
}

export function isQARecord(obj: any): obj is QARecord {
  return obj && typeof obj.task_id === 'string' && Array.isArray(obj.rounds);
}

export function hasError<T>(
  response: ApiResponse<T>
): response is ApiResponse<T> & { error: ErrorDetail } {
  return !response.success && !!response.error;
}
```

### Python Type Utilities
```python
# backend/core/types.py
from typing import TypeVar, Generic, Optional
from pydantic import BaseModel

T = TypeVar('T')

class Result(BaseModel, Generic[T]):
    """Result wrapper for service operations"""
    value: Optional[T] = None
    error: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return self.error is None

    @property
    def is_failure(self) -> bool:
        return self.error is not None

    @classmethod
    def success(cls, value: T) -> "Result[T]":
        return cls(value=value)

    @classmethod
    def failure(cls, error: str) -> "Result[T]":
        return cls(error=error)
```

---

*Data models define the contract between frontend and backend*
*All models must maintain compatibility with Edison's file formats*
*Last Updated: December 2024*
