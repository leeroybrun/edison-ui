"use client";

import type { TrackingRun, RunType } from "./types";

/**
 * Type badge color mappings
 */
const TYPE_COLORS: Record<RunType, string> = {
  implementation: "bg-blue-100 text-blue-800",
  validation: "bg-purple-100 text-purple-800",
  orchestrator: "bg-orange-100 text-orange-800",
};

export interface AgentCardProps {
  /** Run data to display */
  run: TrackingRun;
}

/**
 * Format relative time from ISO date string
 */
function formatRelativeTime(isoDate: string): string {
  const date = new Date(isoDate);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) {
    return "just now";
  } else if (diffMinutes < 60) {
    return `${diffMinutes} min ago`;
  } else if (diffHours < 24) {
    return `${diffHours} hr ago`;
  } else {
    return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
  }
}

/**
 * Get status display information
 */
function getStatusInfo(run: TrackingRun): {
  label: string;
  dotColor: string;
} {
  if (!run.isRunning) {
    return { label: "Stopped", dotColor: "bg-gray-400" };
  }
  if (run.isStale) {
    return { label: "Stale", dotColor: "bg-yellow-500" };
  }
  return { label: "Active", dotColor: "bg-green-500" };
}

/**
 * AgentCard displays a single agent/run in card format.
 *
 * Features:
 * - Shows run ID, type badge, and status indicator
 * - Displays task/session associations
 * - Shows validator info when applicable
 * - Relative time for last activity
 */
export function AgentCard({ run }: AgentCardProps) {
  const statusInfo = getStatusInfo(run);

  return (
    <article className="rounded-lg border bg-white p-4 transition-shadow hover:shadow-md">
      {/* Header with run ID, type badge, and status */}
      <div className="mb-3 flex items-start justify-between">
        <div className="flex items-center gap-2">
          <span
            aria-label={`Status: ${statusInfo.label}`}
            className={`h-2.5 w-2.5 rounded-full ${statusInfo.dotColor}`}
            data-testid="status-dot"
          />
          <span className="font-mono text-sm font-medium text-gray-900">
            {run.runId}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${TYPE_COLORS[run.type]}`}
            data-type={run.type}
          >
            {run.type}
          </span>
          <span className="text-xs text-gray-500">{statusInfo.label}</span>
        </div>
      </div>

      {/* Task and Session info */}
      <div className="mb-3 space-y-1">
        {run.taskId && (
          <div className="flex items-center text-sm text-gray-700">
            <svg
              aria-hidden="true"
              className="mr-1.5 h-4 w-4 text-gray-400"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              viewBox="0 0 24 24"
            >
              <path
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <span>Task: {run.taskId}</span>
          </div>
        )}
        {run.sessionId && (
          <div className="flex items-center text-sm text-gray-700">
            <svg
              aria-hidden="true"
              className="mr-1.5 h-4 w-4 text-gray-400"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              viewBox="0 0 24 24"
            >
              <path
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <span>Session: {run.sessionId}</span>
          </div>
        )}
      </div>

      {/* Validator info (for validation runs) */}
      {run.type === "validation" && run.validatorId && (
        <div className="mb-3 flex items-center gap-2 text-sm text-gray-700">
          <svg
            aria-hidden="true"
            className="h-4 w-4 text-gray-400"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            viewBox="0 0 24 24"
          >
            <path
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <span>Validator: {run.validatorId}</span>
          {run.round !== null && (
            <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs font-medium text-gray-600">
              Round {run.round}
            </span>
          )}
        </div>
      )}

      {/* Metadata footer */}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 border-t pt-3 text-xs text-gray-500">
        {run.model && (
          <span className="flex items-center">
            <svg
              aria-hidden="true"
              className="mr-1 h-3 w-3"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              viewBox="0 0 24 24"
            >
              <path
                d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            {run.model}
          </span>
        )}
        <span className="flex items-center">
          <svg
            aria-hidden="true"
            className="mr-1 h-3 w-3"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            viewBox="0 0 24 24"
          >
            <path
              d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          {run.hostname}
        </span>
        <span
          className="flex items-center"
          data-testid="last-active-time"
          title={new Date(run.lastActiveAt).toLocaleString()}
        >
          <svg
            aria-hidden="true"
            className="mr-1 h-3 w-3"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            viewBox="0 0 24 24"
          >
            <path
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          {formatRelativeTime(run.lastActiveAt)}
        </span>
      </div>
    </article>
  );
}
