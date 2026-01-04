"use client";

import type { ChangeEvent } from "react";

import type { AuditFiltersState, Session, TaskRef } from "./types";

/**
 * Common event types for filtering
 */
const EVENT_TYPES = [
  "task.transition",
  "task.create",
  "task.update",
  "session.start",
  "session.end",
  "qa.transition",
  "cli.invocation.start",
  "cli.invocation.end",
];

export interface AuditFiltersProps {
  /** Current filter values */
  filters: AuditFiltersState;
  /** Callback when any filter changes */
  onChange: (filters: Partial<AuditFiltersState>) => void;
  /** Available sessions for dropdown */
  sessions: Session[];
  /** Available tasks for dropdown */
  tasks: TaskRef[];
}

/**
 * AuditFilters provides filter controls for the audit/activity view.
 *
 * Features:
 * - Session selector
 * - Task selector
 * - Event type selector
 * - Date range picker
 * - Accessible labels on all controls
 */
export function AuditFilters({
  filters,
  onChange,
  sessions,
  tasks,
}: AuditFiltersProps) {
  const handleSessionChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    onChange({ sessionId: value || undefined });
  };

  const handleTaskChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    onChange({ taskId: value || undefined });
  };

  const handleEventTypeChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    onChange({ eventType: value || undefined });
  };

  const handleSinceChange = (event: ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    onChange({ since: value || undefined });
  };

  return (
    <div className="flex flex-wrap gap-4">
      {/* Session filter */}
      <div className="flex flex-col">
        <label className="sr-only" htmlFor="session-filter">
          Filter by session
        </label>
        <select
          aria-label="Filter by session"
          className="h-9 rounded-md border border-gray-300 bg-white px-3 pr-8 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          id="session-filter"
          onChange={handleSessionChange}
          value={filters.sessionId || ""}
        >
          <option value="">All sessions</option>
          {sessions.map((session) => (
            <option key={session.sessionId} value={session.sessionId}>
              {session.name || session.sessionId}
            </option>
          ))}
        </select>
      </div>

      {/* Task filter */}
      <div className="flex flex-col">
        <label className="sr-only" htmlFor="task-filter">
          Filter by task
        </label>
        <select
          aria-label="Filter by task"
          className="h-9 rounded-md border border-gray-300 bg-white px-3 pr-8 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          id="task-filter"
          onChange={handleTaskChange}
          value={filters.taskId || ""}
        >
          <option value="">All tasks</option>
          {tasks.map((task) => (
            <option key={task.taskId} value={task.taskId}>
              {task.taskId} - {task.title}
            </option>
          ))}
        </select>
      </div>

      {/* Event type filter */}
      <div className="flex flex-col">
        <label className="sr-only" htmlFor="event-type-filter">
          Filter by event type
        </label>
        <select
          aria-label="Filter by event type"
          className="h-9 rounded-md border border-gray-300 bg-white px-3 pr-8 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          id="event-type-filter"
          onChange={handleEventTypeChange}
          value={filters.eventType || ""}
        >
          <option value="">All event types</option>
          {EVENT_TYPES.map((eventType) => (
            <option key={eventType} value={eventType}>
              {eventType}
            </option>
          ))}
        </select>
      </div>

      {/* Since date filter */}
      <div className="flex flex-col">
        <label className="sr-only" htmlFor="since-filter">
          Filter by date (since)
        </label>
        <input
          aria-label="Filter by date (since)"
          className="h-9 rounded-md border border-gray-300 px-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          id="since-filter"
          onChange={handleSinceChange}
          type="date"
          value={filters.since || ""}
        />
      </div>
    </div>
  );
}
