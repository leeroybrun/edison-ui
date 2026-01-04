"use client";

import type { KeyboardEvent } from "react";

import type { QARecord, QAState, QAVerdict } from "./types";

/**
 * State badge color mappings
 */
const STATE_COLORS: Record<QAState, string> = {
  waiting: "bg-yellow-100 text-yellow-800",
  todo: "bg-gray-100 text-gray-800",
  wip: "bg-blue-100 text-blue-800",
  done: "bg-green-100 text-green-800",
  validated: "bg-purple-100 text-purple-800",
};

/**
 * Verdict badge color mappings
 */
const VERDICT_COLORS: Record<NonNullable<QAVerdict>, string> = {
  passed: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  in_progress: "bg-blue-100 text-blue-800",
};

export interface QACardProps {
  /** QA record data to display */
  qa: QARecord;
  /** Whether the card is currently selected */
  isSelected?: boolean;
  /** Callback when card is clicked */
  onClick?: (qaId: string) => void;
}

/**
 * QACard displays a single QA record in card format.
 *
 * Features:
 * - Shows QA ID, task ID, state badge, and verdict badge
 * - Displays round number and validators
 * - Displays session ID when present
 * - Supports click and keyboard interaction
 * - Visual indicator for selected state
 */
export function QACard({ qa, isSelected = false, onClick }: QACardProps) {
  const handleClick = () => {
    onClick?.(qa.qaId);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onClick?.(qa.qaId);
    }
  };

  return (
    <article
      className={`rounded-lg border bg-white p-4 transition-shadow hover:shadow-md ${
        isSelected ? "ring-2 ring-blue-500" : ""
      } ${onClick ? "cursor-pointer" : ""}`}
      data-selected={isSelected || undefined}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      tabIndex={onClick ? 0 : undefined}
    >
      {/* Header with QA ID and state badge */}
      <div className="mb-2 flex items-start justify-between">
        <span className="font-mono text-sm font-medium text-gray-900">
          {qa.qaId}
        </span>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATE_COLORS[qa.state]}`}
          data-state={qa.state}
        >
          {qa.state}
        </span>
      </div>

      {/* Task ID */}
      <div className="mb-2 flex items-center gap-2">
        <span className="text-sm text-gray-600">Task:</span>
        <span className="font-mono text-sm font-medium text-gray-900">
          {qa.taskId}
        </span>
      </div>

      {/* Verdict badge */}
      {qa.verdict && (
        <div className="mb-2">
          <span
            className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${VERDICT_COLORS[qa.verdict]}`}
            data-testid="verdict-badge"
          >
            {qa.verdict}
          </span>
        </div>
      )}

      {/* Round number */}
      <div className="mb-2 text-xs text-gray-500">Round {qa.round}</div>

      {/* Validators */}
      <div className="mb-2">
        {qa.validators.length > 0 ? (
          <div className="flex flex-wrap gap-1">
            {qa.validators.map((validator) => (
              <span
                className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600"
                key={validator}
              >
                {validator}
              </span>
            ))}
          </div>
        ) : (
          <span className="text-xs text-gray-400">No validators assigned</span>
        )}
      </div>

      {/* Session ID if present */}
      {qa.sessionId && (
        <div className="flex items-center text-xs text-gray-500">
          <svg
            className="mr-1 h-3 w-3"
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
          <span>{qa.sessionId}</span>
        </div>
      )}
    </article>
  );
}
