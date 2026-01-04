"use client";

import type { TaskQAPanelProps, QAVerdict, QAState } from "./types";
import { RoundTimeline } from "./RoundTimeline";

/**
 * Color mappings for verdict badges
 */
const VERDICT_COLORS: Record<NonNullable<QAVerdict>, string> = {
  passed: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  in_progress: "bg-yellow-100 text-yellow-800",
};

/**
 * Color mappings for state badges
 */
const STATE_COLORS: Record<QAState, string> = {
  waiting: "bg-gray-100 text-gray-800",
  todo: "bg-gray-100 text-gray-800",
  wip: "bg-blue-100 text-blue-800",
  done: "bg-green-100 text-green-800",
  validated: "bg-purple-100 text-purple-800",
};

/**
 * Loading spinner component
 */
function LoadingSpinner() {
  return (
    <div
      className="flex items-center justify-center py-8"
      data-testid="qa-panel-loading"
    >
      <svg
        className="h-8 w-8 animate-spin text-blue-500"
        fill="none"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
      <span className="ml-2 text-gray-600">Loading QA data...</span>
    </div>
  );
}

/**
 * Error display component
 */
function ErrorDisplay({ error }: { error: Error }) {
  return (
    <div
      className="rounded-lg border border-red-200 bg-red-50 p-4"
      data-testid="qa-panel-error"
    >
      <div className="flex items-center">
        <svg
          className="h-5 w-5 text-red-500"
          fill="currentColor"
          viewBox="0 0 20 20"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
            clipRule="evenodd"
          />
        </svg>
        <span className="ml-2 text-sm text-red-700">{error.message}</span>
      </div>
    </div>
  );
}

/**
 * Empty state component
 */
function EmptyState() {
  return (
    <div
      className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center"
      data-testid="qa-panel-empty"
    >
      <svg
        className="mx-auto h-12 w-12 text-gray-400"
        fill="none"
        stroke="currentColor"
        strokeWidth={1.5}
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z"
        />
      </svg>
      <p className="mt-2 text-sm text-gray-600">No QA record for this task</p>
      <p className="mt-1 text-xs text-gray-500">
        QA will appear once validation begins
      </p>
    </div>
  );
}

/**
 * TaskQAPanel displays QA validation information for a task.
 *
 * Features:
 * - Displays QA ID, state, and verdict
 * - Shows validation rounds timeline
 * - Expandable round details with validator reports
 * - Evidence artifacts with redacted paths
 * - Loading and error states
 * - Empty state when no QA exists
 */
export function TaskQAPanel({
  qa,
  isLoading = false,
  error = null,
}: TaskQAPanelProps) {
  // Loading state
  if (isLoading) {
    return <LoadingSpinner />;
  }

  // Error state
  if (error) {
    return <ErrorDisplay error={error} />;
  }

  // Empty state
  if (!qa) {
    return <EmptyState />;
  }

  const verdictColorClass = qa.verdict
    ? VERDICT_COLORS[qa.verdict]
    : "bg-gray-100 text-gray-800";
  const stateColorClass = STATE_COLORS[qa.state];

  return (
    <section className="rounded-lg border border-gray-200 bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <h3 className="text-lg font-semibold text-gray-900">QA Validation</h3>
      </div>

      {/* QA Info */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex flex-wrap items-center gap-4">
          {/* QA ID */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">ID:</span>
            <span className="font-mono text-sm font-medium text-gray-900">
              {qa.qaId}
            </span>
          </div>

          {/* State Badge */}
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${stateColorClass}`}
          >
            {qa.state}
          </span>

          {/* Verdict Badge */}
          {qa.verdict && (
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-medium ${verdictColorClass}`}
              data-testid="verdict-badge"
            >
              {qa.verdict}
            </span>
          )}

          {/* Current Round */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">Round {qa.round}</span>
          </div>
        </div>

        {/* Validators */}
        {qa.validators.length > 0 && (
          <div className="mt-3">
            <span className="text-sm text-gray-500">Validators: </span>
            <span className="text-sm text-gray-700">
              {qa.validators.map((v, i) => (
                <span key={v}>
                  {i > 0 && ", "}
                  <span className="font-medium">{v}</span>
                </span>
              ))}
            </span>
          </div>
        )}
      </div>

      {/* Rounds Timeline */}
      <div className="p-4">
        <h4 className="mb-3 text-sm font-medium text-gray-700">
          Validation Rounds
        </h4>
        <RoundTimeline
          evidence={qa.evidence}
          currentRound={qa.round}
          verdict={qa.verdict}
        />
      </div>
    </section>
  );
}
