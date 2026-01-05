"use client";

import { useCallback, useMemo } from "react";
import { useRouter, usePathname } from "next/navigation";

import { SessionCard } from "./SessionCard";
import type {
  Session,
  SessionsViewProps,
  SessionState,
  ViewMode,
} from "./types";

/**
 * All valid session states matching backend SESSION_STATES
 */
const SESSION_STATES: SessionState[] = [
  "draft",
  "active",
  "paused",
  "completed",
  "abandoned",
];

/**
 * State badge color mappings for list view
 */
const STATE_COLORS: Record<SessionState, string> = {
  draft: "bg-gray-100 text-gray-800",
  active: "bg-blue-100 text-blue-800",
  paused: "bg-yellow-100 text-yellow-800",
  completed: "bg-green-100 text-green-800",
  abandoned: "bg-red-100 text-red-800",
};

/**
 * Column display names for board view
 */
const COLUMN_LABELS: Record<SessionState, string> = {
  draft: "Draft",
  active: "Active",
  paused: "Paused",
  completed: "Completed",
  abandoned: "Abandoned",
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
 * SessionsView displays sessions in list or board format with filtering.
 *
 * Features:
 * - Toggle between list (table) and board (kanban) views
 * - Filter by session state (draft, active, paused, completed, abandoned)
 * - URL-based view and filter state
 * - Clickable sessions navigate to detail view
 * - Loading, error, and empty states
 */
export function SessionsView({
  projectId,
  sessions,
  initialView = "list",
  initialStateFilter,
  error,
  isLoading = false,
}: SessionsViewProps) {
  const router = useRouter();
  const pathname = usePathname();

  // Build URL with query params
  const buildUrl = useCallback(
    (view: ViewMode, stateFilter?: SessionState) => {
      const params = new URLSearchParams();
      params.set("view", view);
      if (stateFilter) {
        params.set("state", stateFilter);
      }
      return `${pathname}?${params.toString()}`;
    },
    [pathname],
  );

  // Filter sessions by state
  const filteredSessions = useMemo(() => {
    if (!initialStateFilter) return sessions;
    return sessions.filter((s) => s.state === initialStateFilter);
  }, [sessions, initialStateFilter]);

  // Group sessions by state for board view
  const sessionsByState = useMemo(() => {
    const grouped: Record<SessionState, Session[]> = {
      draft: [],
      active: [],
      paused: [],
      completed: [],
      abandoned: [],
    };
    filteredSessions.forEach((session) => {
      grouped[session.state].push(session);
    });
    return grouped;
  }, [filteredSessions]);

  // Handle view toggle
  const handleViewChange = (view: ViewMode) => {
    router.push(buildUrl(view, initialStateFilter));
  };

  // Handle state filter
  const handleStateFilter = (state?: SessionState) => {
    router.push(buildUrl(initialView, state));
  };

  // Handle session click - navigate to Tasks view filtered by this session
  // Per spec: "selecting a session shows that session's tasks"
  const handleSessionClick = (sessionId: string) => {
    router.push(`/projects/${projectId}/tasks?sessionId=${sessionId}`);
  };

  // Handle row keyboard navigation
  const handleRowKeyDown = (event: React.KeyboardEvent, sessionId: string) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      handleSessionClick(sessionId);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold text-gray-900">Sessions</h1>
        <div className="flex items-center justify-center py-12">
          <span className="text-gray-500">Loading sessions...</span>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold text-gray-900">Sessions</h1>
        <div
          className="rounded-lg border border-red-200 bg-red-50 p-4"
          role="alert"
        >
          <p className="text-red-700">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">Sessions</h1>

        {/* View toggle */}
        <div className="flex rounded-lg border bg-white p-1">
          <button
            aria-pressed={initialView === "list"}
            className={`rounded px-3 py-1.5 text-sm font-medium transition-colors ${
              initialView === "list"
                ? "bg-blue-50 text-blue-700"
                : "text-gray-600 hover:bg-gray-50"
            }`}
            onClick={() => handleViewChange("list")}
            type="button"
          >
            List View
          </button>
          <button
            aria-pressed={initialView === "board"}
            className={`rounded px-3 py-1.5 text-sm font-medium transition-colors ${
              initialView === "board"
                ? "bg-blue-50 text-blue-700"
                : "text-gray-600 hover:bg-gray-50"
            }`}
            onClick={() => handleViewChange("board")}
            type="button"
          >
            Board View
          </button>
        </div>
      </div>

      {/* State filters */}
      <div className="flex gap-2">
        <button
          aria-pressed={!initialStateFilter}
          className={`rounded-full px-3 py-1 text-sm font-medium transition-colors ${
            !initialStateFilter
              ? "bg-gray-900 text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
          onClick={() => handleStateFilter(undefined)}
          type="button"
        >
          All States
        </button>
        {SESSION_STATES.map((state) => (
          <button
            key={state}
            aria-pressed={initialStateFilter === state}
            className={`rounded-full px-3 py-1 text-sm font-medium transition-colors ${
              initialStateFilter === state
                ? "bg-gray-900 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
            onClick={() => handleStateFilter(state)}
            type="button"
          >
            {COLUMN_LABELS[state]}
          </button>
        ))}
      </div>

      {/* Empty state */}
      {filteredSessions.length === 0 && (
        <div className="rounded-lg border bg-white p-8 text-center">
          <p className="text-gray-500">No sessions found</p>
          {initialStateFilter && (
            <p className="mt-2 text-sm text-gray-400">
              Try clearing the filter to see all sessions
            </p>
          )}
        </div>
      )}

      {/* List view */}
      {initialView === "list" && filteredSessions.length > 0 && (
        <div className="overflow-hidden rounded-lg border bg-white">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th
                  className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                  scope="col"
                >
                  Session ID
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                  scope="col"
                >
                  State
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                  scope="col"
                >
                  Phase
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                  scope="col"
                >
                  Tasks
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                  scope="col"
                >
                  Last Active
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {filteredSessions.map((session) => (
                <tr
                  key={session.sessionId}
                  className="cursor-pointer transition-colors hover:bg-gray-50"
                  onClick={() => handleSessionClick(session.sessionId)}
                  onKeyDown={(e) => handleRowKeyDown(e, session.sessionId)}
                  tabIndex={0}
                >
                  <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">
                    {session.sessionId}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATE_COLORS[session.state]}`}
                    >
                      {session.state}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {session.phase}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {session.taskCount}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {formatRelativeTime(session.lastActiveAt)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Board view */}
      {initialView === "board" && filteredSessions.length > 0 && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
          {SESSION_STATES.map((state) => (
            <div
              key={state}
              className="rounded-lg border bg-gray-50 p-4"
              data-testid={`column-${state}`}
            >
              {/* Column header */}
              <div className="mb-4 flex items-center justify-between">
                <h2 className="font-semibold text-gray-900">
                  {COLUMN_LABELS[state]}
                </h2>
                <span className="rounded-full bg-gray-200 px-2 py-0.5 text-xs font-medium text-gray-600">
                  {sessionsByState[state].length}
                </span>
              </div>

              {/* Session cards */}
              <div className="space-y-3">
                {sessionsByState[state].map((session) => (
                  <SessionCard
                    key={session.sessionId}
                    onClick={handleSessionClick}
                    projectId={projectId}
                    session={session}
                  />
                ))}

                {/* Empty column */}
                {sessionsByState[state].length === 0 && (
                  <p className="py-4 text-center text-sm text-gray-400">
                    No sessions
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
