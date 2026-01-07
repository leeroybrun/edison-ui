/**
 * Agent/Run types matching backend API schemas.
 */

/**
 * Type of agent run
 */
export type RunType = "implementation" | "validation" | "orchestrator";

/**
 * State of an agent run
 */
export type RunState = "active" | "stopped";

/**
 * Represents a tracking run (agent/validator instance)
 */
export interface TrackingRun {
  runId: string;
  type: RunType;
  taskId: string | null;
  sessionId: string | null;
  validatorId: string | null;
  round: number | null;
  model: string | null;
  processId: number;
  hostname: string;
  startedAt: string;
  lastActiveAt: string;
  isRunning: boolean;
  isStale: boolean;
  state: RunState;
}

/**
 * API response for agents list endpoint
 */
export interface AgentsListResponse {
  items: TrackingRun[];
  total: number;
}

/**
 * Filter state for agents
 */
export interface AgentFilters {
  sessionId?: string;
  taskId?: string;
  type?: RunType;
}
