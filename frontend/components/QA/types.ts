/**
 * QA types matching backend API schemas.
 */

/**
 * Possible states for a QA record
 */
export type QAState = "waiting" | "todo" | "wip" | "done" | "validated";

/**
 * Possible verdicts for a QA record
 */
export type QAVerdict = "passed" | "rejected" | "in_progress" | null;

/**
 * Single QA record item
 */
export interface QARecord {
  qaId: string;
  taskId: string;
  sessionId: string | null;
  round: number;
  state: QAState;
  verdict: QAVerdict;
  validators: string[];
  createdAt: string;
  updatedAt: string;
}

/**
 * Session reference for filtering (shared with Tasks)
 */
export interface Session {
  sessionId: string;
  name: string;
}

/**
 * API response for QA list endpoint
 */
export interface QAListResponse {
  items: QARecord[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * View modes for the QA view
 */
export type ViewMode = "list" | "board";

/**
 * Filter state for QA records
 */
export interface QAFilters {
  state?: QAState;
  verdict?: string;
  sessionId?: string;
  validator?: string;
  search?: string;
}

/**
 * Validator verdict for a specific validator report
 */
export type ValidatorVerdict = "pass" | "fail";

/**
 * Single validator report within a round
 */
export interface ValidatorReport {
  validatorId: string;
  verdict: ValidatorVerdict;
  reason: string;
  reportPath: string;
}

/**
 * Artifact within a round's evidence
 */
export interface EvidenceArtifact {
  name: string;
  path: string;
  type: string;
}

/**
 * Evidence for a single round
 */
export interface RoundEvidence {
  roundNumber: number;
  bundleSummary: string;
  implementationReport: string | null;
  validatorReports: ValidatorReport[];
  artifacts: EvidenceArtifact[];
}

/**
 * State history entry
 */
export interface QAStateHistoryEntry {
  state: QAState;
  timestamp: string;
  actor?: string;
}

/**
 * Full QA detail response from API (for task detail page)
 */
export interface TaskQADetailResponse {
  qaId: string;
  taskId: string;
  sessionId: string | null;
  round: number;
  state: QAState;
  verdict: QAVerdict;
  validators: string[];
  evidence: RoundEvidence[];
  stateHistory: QAStateHistoryEntry[];
  createdAt: string;
  updatedAt: string;
}

/**
 * Props for TaskQAPanel component
 */
export interface TaskQAPanelProps {
  /** QA data to display */
  qa: TaskQADetailResponse | null;
  /** Loading state */
  isLoading?: boolean;
  /** Error state */
  error?: Error | null;
}

/**
 * Props for RoundTimeline component
 */
export interface RoundTimelineProps {
  /** Evidence from all rounds */
  evidence: RoundEvidence[];
  /** Current round number */
  currentRound: number;
  /** Overall verdict */
  verdict: QAVerdict;
}

/**
 * Props for individual RoundItem component
 */
export interface RoundItemProps {
  /** Evidence for this round */
  round: RoundEvidence;
  /** Whether this is the current/latest round */
  isCurrent: boolean;
  /** Whether this round is expanded */
  isExpanded: boolean;
  /** Callback when expand/collapse is toggled */
  onToggle: () => void;
}
