"use client";

import type { KeyboardEvent } from "react";
import { useState } from "react";

import type { Task, TaskState } from "./types";

/**
 * State badge color mappings
 */
const STATE_COLORS: Record<TaskState, string> = {
  todo: "bg-gray-100 text-gray-800",
  wip: "bg-blue-100 text-blue-800",
  blocked: "bg-red-100 text-red-800",
  done: "bg-green-100 text-green-800",
  validated: "bg-purple-100 text-purple-800",
};

export interface TaskCardProps {
  /** Task data to display */
  task: Task;
  /** Whether the card is currently selected */
  isSelected?: boolean;
  /** Callback when card is clicked */
  onClick?: (taskId: string) => void;
}

/**
 * TaskCard displays a single task in card format.
 *
 * Features:
 * - Shows task ID, title, and state badge
 * - Displays session ID when present
 * - Supports click and keyboard interaction
 * - Visual indicator for selected state
 * - Shows Ready/Blocked status with why blocked explanations
 */
export function TaskCard({ task, isSelected = false, onClick }: TaskCardProps) {
  const [showBlockedDetails, setShowBlockedDetails] = useState(false);

  const handleClick = () => {
    onClick?.(task.taskId);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onClick?.(task.taskId);
    }
  };

  const toggleBlockedDetails = (event: React.MouseEvent) => {
    event.stopPropagation();
    setShowBlockedDetails(!showBlockedDetails);
  };

  const toggleBlockedDetailsKeyboard = (
    event: KeyboardEvent<HTMLButtonElement>,
  ) => {
    if (event.key === "Enter" || event.key === " ") {
      event.stopPropagation();
      event.preventDefault();
      setShowBlockedDetails(!showBlockedDetails);
    }
  };

  const isBlocked = !task.ready && task.blockedBy.length > 0;

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
      {/* Header with task ID and state badge */}
      <div className="mb-2 flex items-start justify-between">
        <span className="font-mono text-sm font-medium text-gray-900">
          {task.taskId}
        </span>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATE_COLORS[task.state]}`}
          data-state={task.state}
        >
          {task.state}
        </span>
      </div>

      {/* Task title */}
      <div className="mb-2 text-sm text-gray-900">{task.title}</div>

      {/* Ready/Blocked indicator */}
      <div className="mb-2">
        {task.ready ? (
          <span
            className="inline-flex items-center rounded-full bg-green-50 px-2 py-0.5 text-xs font-medium text-green-700"
            data-testid="ready-badge"
          >
            <svg
              aria-hidden="true"
              className="mr-1 h-3 w-3"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                clipRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                fillRule="evenodd"
              />
            </svg>
            Ready
          </span>
        ) : isBlocked ? (
          <div>
            <button
              aria-expanded={showBlockedDetails}
              aria-label="Show why this task is blocked"
              className="inline-flex items-center rounded-full bg-red-50 px-2 py-0.5 text-xs font-medium text-red-700 hover:bg-red-100"
              data-testid="blocked-badge"
              onClick={toggleBlockedDetails}
              onKeyDown={toggleBlockedDetailsKeyboard}
              type="button"
            >
              <svg
                aria-hidden="true"
                className="mr-1 h-3 w-3"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  clipRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  fillRule="evenodd"
                />
              </svg>
              Blocked ({task.blockedBy.length})
              <svg
                aria-hidden="true"
                className={`ml-1 h-3 w-3 transition-transform ${showBlockedDetails ? "rotate-180" : ""}`}
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
                viewBox="0 0 24 24"
              >
                <path
                  d="M19 9l-7 7-7-7"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
            {showBlockedDetails && (
              <ul
                className="mt-2 space-y-1 text-xs text-red-600"
                data-testid="blocked-reasons"
              >
                {task.blockedBy.map((blocker, index) => (
                  <li key={index} className="flex items-start">
                    <span className="mr-1">•</span>
                    <span>{blocker.reason}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ) : null}
      </div>

      {/* Session ID if present */}
      {task.sessionId && (
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
          <span>{task.sessionId}</span>
        </div>
      )}
    </article>
  );
}
