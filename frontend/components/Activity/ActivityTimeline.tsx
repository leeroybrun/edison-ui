"use client";

import type { ActivityItem } from "./types";

/**
 * Event type to badge color mappings
 */
const EVENT_TYPE_COLORS: Record<string, string> = {
  "task.transition": "bg-blue-100 text-blue-800",
  "task.create": "bg-green-100 text-green-800",
  "task.update": "bg-yellow-100 text-yellow-800",
  "session.start": "bg-purple-100 text-purple-800",
  "session.end": "bg-purple-100 text-purple-800",
  "qa.transition": "bg-orange-100 text-orange-800",
  default: "bg-gray-100 text-gray-800",
};

/**
 * Get badge color for event type
 */
function getEventTypeColor(eventType: string): string {
  return EVENT_TYPE_COLORS[eventType] || EVENT_TYPE_COLORS.default;
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
  });
}

export interface ActivityTimelineProps {
  /** Activity items to display */
  items: ActivityItem[];
  /** Whether the timeline is loading */
  loading: boolean;
  /** Whether there are more items to load */
  hasMore: boolean;
  /** Callback when Load more is clicked */
  onLoadMore: () => void;
}

/**
 * ActivityTimeline displays a vertical timeline of activity events.
 *
 * Features:
 * - Vertical timeline with timestamps
 * - Event icons based on eventType
 * - Actor badges
 * - "Load more" for pagination
 * - Accessible list structure
 */
export function ActivityTimeline({
  items,
  loading,
  hasMore,
  onLoadMore,
}: ActivityTimelineProps) {
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
          <span>Loading activity...</span>
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
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <p>No activity found</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <ul className="space-y-4" role="list">
        {items.map((item, index) => (
          <li
            key={`${item.invocationId}-${index}`}
            className="relative flex gap-4 rounded-lg border bg-white p-4 shadow-sm"
          >
            {/* Timeline line */}
            {index < items.length - 1 && (
              <div
                aria-hidden="true"
                className="absolute left-8 top-16 h-full w-0.5 bg-gray-200"
              />
            )}

            {/* Timeline dot */}
            <div className="flex-shrink-0">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-100">
                <svg
                  aria-hidden="true"
                  className="h-4 w-4 text-gray-600"
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
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 space-y-2">
              {/* Header: timestamp and event type */}
              <div className="flex flex-wrap items-center gap-2">
                <time
                  className="text-sm text-gray-500"
                  dateTime={item.timestamp}
                >
                  {formatTimestamp(item.timestamp)}
                </time>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${getEventTypeColor(item.eventType)}`}
                >
                  {item.eventType}
                </span>
              </div>

              {/* Summary */}
              <p className="text-sm text-gray-900">{item.summary}</p>

              {/* Metadata: actor, session, task */}
              <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
                {/* Actor */}
                <span className="flex items-center gap-1">
                  <svg
                    aria-hidden="true"
                    className="h-3 w-3"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={2}
                    viewBox="0 0 24 24"
                  >
                    <path
                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                  <span>{item.actor.displayName}</span>
                </span>

                {/* Session ID */}
                {item.sessionId && (
                  <span className="flex items-center gap-1">
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

                {/* Task ID */}
                {item.taskId && (
                  <span className="flex items-center gap-1">
                    <svg
                      aria-hidden="true"
                      className="h-3 w-3"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth={2}
                      viewBox="0 0 24 24"
                    >
                      <path
                        d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                    <span>{item.taskId}</span>
                  </span>
                )}
              </div>
            </div>
          </li>
        ))}
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
