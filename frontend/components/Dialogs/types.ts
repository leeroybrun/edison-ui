/**
 * Dialog and mutation flow types matching backend API guard schemas.
 */

/**
 * Represents a guard failure from the API
 */
export interface GuardFailure {
  guard: string;
  reason: string;
}

/**
 * Represents a guard warning (non-blocking)
 */
export interface GuardWarning {
  guard: string;
  message: string;
}

/**
 * Preview response from a transition/mutation endpoint
 */
export interface TransitionPreview {
  allowed: boolean;
  from: string;
  to: string;
  guardFailures: GuardFailure[];
  guardWarnings: GuardWarning[];
  requiresConfirmation: boolean;
}

/**
 * Task creation preview response
 */
export interface TaskCreatePreview {
  allowed: boolean;
  taskId: string;
  title: string;
  guardFailures: GuardFailure[];
  guardWarnings: GuardWarning[];
}

/**
 * Transition result from confirmed mutation
 */
export interface TransitionResult {
  success: boolean;
  taskId: string;
  fromState: string;
  toState: string;
  message?: string;
}

/**
 * Task creation result
 */
export interface TaskCreateResult {
  success: boolean;
  taskId: string;
  title: string;
  state: string;
  message?: string;
}

/**
 * Dialog state for preview/confirm flow
 */
export type DialogState =
  | "idle"
  | "loading"
  | "preview"
  | "confirming"
  | "success"
  | "error";
