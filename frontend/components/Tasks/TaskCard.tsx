"use client";

import type { KeyboardEvent } from "react";

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
 */
export function TaskCard({ task, isSelected = false, onClick }: TaskCardProps) {
  const handleClick = () => {
    onClick?.(task.taskId);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onClick?.(task.taskId);
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
