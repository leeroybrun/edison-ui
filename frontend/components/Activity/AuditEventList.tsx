"use client";

import { useState } from "react";

import type { AuditEvent } from "./types";

/**
 * Format duration in human-readable format
 */
function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`;
  }
  return `${(ms / 1000).toFixed(1)}s`;
}

/**
 * Format timestamp to human-readable format
 */
function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

/**
 * Get exit code badge color
 */
function getExitCodeColor(exitCode: number): string {
  if (exitCode === 0) {
    return "bg-green-100 text-green-800";
  }
  return "bg-red-100 text-red-800";
}

export interface AuditEventListProps {
  /** Audit events to display */
  items: AuditEvent[];
  /** Whether the list is loading */
  loading: boolean;
  /** Whether there are more items to load */
  hasMore: boolean;
  /** Callback when Load more is clicked */
  onLoadMore: () => void;
  /** Whether to show raw/detailed view */
  showRaw: boolean;
}

/**
 * AuditEventList displays raw audit events in a list format.
 *
 * Features:
 * - Collapsible event details
 * - Command/exit code display
 * - Duration badges
 * - Toggle between high-level and raw views
 * - Accessible list structure
 */
export function AuditEventList({
  items,
  loading,
  hasMore,
  onLoadMore,
  showRaw,
}: AuditEventListProps) {
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  const toggleExpanded = (invocationId: string) => {
    setExpandedItems((prev) => {
      const next = new Set(prev);
      if (next.has(invocationId)) {
        next.delete(invocationId);
      } else {
        next.add(invocationId);
      }
      return next;
    });
  };

  if (loading && items.length === 0) {
    return (
      <div className="flex items-center justify-center py-12" role="status">
        <div className="flex items-center space-x-2 text-gray-500">
          <svg
            aria-hidden="true"
            className="h-5 w-5 animate-spin"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            viewBox="0 0 24 24"
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
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              fill="currentColor"
            />
          </svg>
          <span>Loading audit events...</span>
        </div>
      </div>
    );
  }

  if (!loading && items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-gray-500">
        <svg
          aria-hidden="true"
          className="mb-4 h-12 w-12"
          fill="none"
          stroke="currentColor"
          strokeWidth={1.5}
          viewBox="0 0 24 24"
        >
          <path
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <p>No audit events found</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <ul className="space-y-2" role="list">
        {items.map((item, index) => {
          const isExpanded = expandedItems.has(item.invocationId) || showRaw;

          return (
            <li
              key={`${item.invocationId}-${index}`}
              className="rounded-lg border bg-white shadow-sm"
            >
              {/* Main row */}
              <div className="flex items-center gap-4 p-4">
                {/* Event type */}
                <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-800">
                  {item.event}
                </span>

                {/* Command (truncated) */}
                <span className="flex-1 truncate font-mono text-sm text-gray-700">
                  {item.command}
                </span>

                {/* Exit code badge */}
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${getExitCodeColor(item.exitCode)}`}
                  title={`Exit code: ${item.exitCode}`}
                >
                  {item.exitCode}
                </span>

                {/* Duration */}
                <span className="text-xs text-gray-500">
                  {formatDuration(item.durationMs)}
                </span>

                {/* Session ID if present */}
                {item.sessionId && (
                  <span className="flex items-center gap-1 text-xs text-gray-500">
                    <svg
                      aria-hidden="true"
                      className="h-3 w-3"
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
                    <span>{item.sessionId}</span>
                  </span>
                )}

                {/* Expand/collapse button */}
                <button
                  aria-expanded={isExpanded}
                  aria-label={
                    isExpanded ? "Collapse details" : "Expand details"
                  }
                  className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                  onClick={() => toggleExpanded(item.invocationId)}
                  type="button"
                >
                  <svg
                    aria-hidden="true"
                    className={`h-4 w-4 transition-transform ${isExpanded ? "rotate-180" : ""}`}
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
              </div>

              {/* Expanded details */}
              {isExpanded && (
                <div className="border-t bg-gray-50 px-4 py-3">
                  <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                    <div>
                      <dt className="text-gray-500">Invocation ID</dt>
                      <dd className="font-mono text-gray-900">
                        {item.invocationId}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-gray-500">Timestamp</dt>
                      <dd className="text-gray-900">
                        {formatTimestamp(item.ts)}
                      </dd>
                    </div>
                    <div className="col-span-2">
                      <dt className="text-gray-500">Full Command</dt>
                      <dd className="font-mono text-gray-900">
                        {item.command}
                      </dd>
                    </div>
                    {item.sessionId && (
                      <div>
                        <dt className="text-gray-500">Session ID</dt>
                        <dd className="font-mono text-gray-900">
                          {item.sessionId}
                        </dd>
                      </div>
                    )}
                    <div>
                      <dt className="text-gray-500">Exit Code</dt>
                      <dd className="text-gray-900">{item.exitCode}</dd>
                    </div>
                    <div>
                      <dt className="text-gray-500">Duration</dt>
                      <dd className="text-gray-900">
                        {formatDuration(item.durationMs)} ({item.durationMs}ms)
                      </dd>
                    </div>
                  </dl>
                </div>
              )}
            </li>
          );
        })}
      </ul>

      {/* Load more button */}
      {hasMore && (
        <div className="flex justify-center pt-4">
          <button
            className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            onClick={onLoadMore}
            type="button"
          >
            Load more
          </button>
        </div>
      )}

      {/* Loading indicator for pagination */}
      {loading && items.length > 0 && (
        <div className="flex justify-center py-4" role="status">
          <span className="text-sm text-gray-500">Loading more...</span>
        </div>
      )}
    </div>
  );
}
