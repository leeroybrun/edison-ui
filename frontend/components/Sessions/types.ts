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
