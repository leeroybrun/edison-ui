/**
 * Activity types matching backend API schemas for audit and activity endpoints.
 */

/**
 * Actor information for activity events
 */
export interface Actor {
  osUser: string;
  displayName: string;
}

/**
 * Activity item from GET /projects/{projectId}/activity
 */
export interface ActivityItem {
  timestamp: string;
  eventType: string;
  summary: string;
  sessionId: string | null;
  taskId: string | null;
  invocationId: string | null;
  actor: Actor;
}

/**
 * Activity API response
 */
export interface ActivityResponse {
  items: ActivityItem[];
  hasMore: boolean;
}

/**
 * Audit event from GET /projects/{projectId}/audit
 */
export interface AuditEvent {
  ts: string;
  event: string;
  invocationId: string;
  sessionId: string | null;
  command: string;
  exitCode: number;
  durationMs: number;
}

/**
 * Audit API response
 */
export interface AuditResponse {
  items: AuditEvent[];
  hasMore: boolean;
}

/**
 * Filter state for audit/activity views
 */
export interface AuditFiltersState {
  sessionId?: string;
  taskId?: string;
  eventType?: string;
  since?: string;
}

/**
 * Session reference for filtering
 */
export interface Session {
  sessionId: string;
  name: string;
}

/**
 * Task reference for filtering
 */
export interface TaskRef {
  taskId: string;
  title: string;
}
