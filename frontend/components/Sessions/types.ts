/**
 * Session types matching backend API schemas.
 */

/**
 * Session states from backend SessionReaderService.
 * These match the directory names under .project/sessions/
 * Must stay in sync with backend VALID_SESSION_STATES.
 */
export type SessionState =
  | "draft"
  | "active"
  | "wip"
  | "blocked"
  | "paused"
  | "done"
  | "closing"
  | "completed"
  | "validated"
  | "archived"
  | "abandoned";

export type ViewMode = "list" | "board";

export interface SessionGit {
  branchName: string;
  baseBranch: string;
}

export interface Session {
  sessionId: string;
  state: SessionState;
  phase: string;
  owner: string | null;
  taskCount: number;
  createdAt: string;
  lastActiveAt: string;
  git: SessionGit;
}

export interface SessionListResponse {
  items: Session[];
  total: number;
  limit: number;
  offset: number;
}

export interface SessionsViewProps {
  /** Project identifier */
  projectId: string;
  /** Initial sessions data */
  sessions: Session[];
  /** Initial view mode from URL */
  initialView?: ViewMode;
  /** Initial state filter from URL */
  initialStateFilter?: SessionState;
  /** Error message if fetch failed */
  error?: string;
  /** Whether data is loading */
  isLoading?: boolean;
}

export interface SessionCardProps {
  /** Session data */
  session: Session;
  /** Project ID for navigation */
  projectId: string;
  /** Whether the session is currently selected */
  isSelected?: boolean;
  /** Callback when session is clicked */
  onClick?: (sessionId: string) => void;
}

/**
 * Session context response from /context endpoint.
 * Contains session state and configuration information.
 */
export interface SessionContextResponse {
  /** Whether this is a valid Edison project */
  isEdisonProject: boolean;
  /** Project root path (may be redacted) */
  projectRoot: string;
  /** Session identifier */
  sessionId: string;
  /** Current session state */
  sessionState: SessionState | string;
  /** Worktree path (may be redacted or null) */
  worktreePath: string | null;
  /** Currently claimed task ID, if any */
  currentTaskId: string | null;
  /** Current task state, if any */
  currentTaskState: string | null;
  /** Active technology packs */
  activePacks: string[];
  /** Constitution name to path mapping */
  constitutions: Record<string, string>;
  /** Timestamp when context was computed (optional) */
  timestamp?: string;
}

/**
 * A suggested action from the session next endpoint.
 */
export interface SuggestedAction {
  /** Type of action to take */
  actionType: "claim" | "validate" | "review" | "complete" | "pause" | string;
  /** Task ID if action is task-related, null otherwise */
  taskId: string | null;
  /** Human-readable reason for the suggestion */
  reason: string;
}

/**
 * Session next response from /next endpoint.
 * Contains recommendations for next steps.
 */
export interface SessionNextResponse {
  /** Markdown-formatted recommendation text */
  recommendation: string;
  /** List of suggested actions */
  suggestedActions: SuggestedAction[];
  /** Timestamp when recommendations were computed */
  timestamp: string;
}

/**
 * Props for SessionContextPanel component.
 */
export interface SessionContextPanelProps {
  /** Project ID for API calls */
  projectId: string;
  /** Session ID for API calls */
  sessionId: string;
}

/**
 * Props for SessionNextPanel component.
 */
export interface SessionNextPanelProps {
  /** Project ID for API calls */
  projectId: string;
  /** Session ID for API calls */
  sessionId: string;
}
