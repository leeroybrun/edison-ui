"use client";

import type { KeyboardEvent } from "react";

import type { SessionCardProps, SessionState } from "./types";

/**
 * State badge color mappings
 */
const STATE_COLORS: Record<SessionState, string> = {
  wip: "bg-yellow-100 text-yellow-800",
  done: "bg-blue-100 text-blue-800",
  validated: "bg-green-100 text-green-800",
};

/**
 * Format relative time from ISO date string
 */
function formatRelativeTime(isoDate: string): string {
  const date = new Date(isoDate);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString();
}

/**
 * SessionCard displays a single session in card format.
 *
 * Features:
 * - Shows session ID, state badge, task count, and last active time
 * - Displays branch name for git context
 * - Supports click and keyboard interaction
 * - Visual indicator for selected state
 */
export function SessionCard({
  session,
  projectId: _projectId,
  isSelected = false,
  onClick,
}: SessionCardProps) {
  const handleClick = () => {
    onClick?.(session.sessionId);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onClick?.(session.sessionId);
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
      {/* Header with session ID and state badge */}
      <div className="mb-2 flex items-start justify-between">
        <span className="font-medium text-gray-900">{session.sessionId}</span>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATE_COLORS[session.state]}`}
        >
          {session.state}
        </span>
      </div>

      {/* Phase */}
      <div className="mb-2 text-sm text-gray-600">{session.phase}</div>

      {/* Branch name */}
      <div className="mb-3 flex items-center text-sm text-gray-500">
        <svg
          className="mr-1.5 h-4 w-4"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          viewBox="0 0 24 24"
        >
          <path
            d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <span className="truncate">{session.git.branchName}</span>
      </div>

      {/* Footer with task count and last active */}
      <div className="flex items-center justify-between text-sm text-gray-500">
        <span>{session.taskCount} tasks</span>
        <span>Last active: {formatRelativeTime(session.lastActiveAt)}</span>
      </div>
    </article>
  );
}
