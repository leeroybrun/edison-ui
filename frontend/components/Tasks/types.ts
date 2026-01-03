/**
 * Task types matching backend API schemas.
 */

/**
 * Possible states for a task
 */
export type TaskState = "todo" | "wip" | "blocked" | "done" | "validated";

/**
 * Single task item
 */
export interface Task {
  taskId: string;
  title: string;
  state: TaskState;
  sessionId: string | null;
  parentId: string | null;
  dependsOn: string[];
  createdAt: string;
  updatedAt: string;
}

/**
 * Session reference for filtering
 */
export interface Session {
  sessionId: string;
  name: string;
}

/**
 * API response for task list endpoint
 */
export interface TaskListResponse {
  items: Task[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * View modes for the tasks view
 */
export type ViewMode = "list" | "board" | "tree";

/**
 * Filter state for tasks
 */
export interface TaskFilters {
  state?: TaskState;
  sessionId?: string;
  search?: string;
}
