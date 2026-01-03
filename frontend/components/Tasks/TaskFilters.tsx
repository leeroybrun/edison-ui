"use client";

import type { ChangeEvent } from "react";

import type { Session, TaskFilters as TaskFiltersType, TaskState } from "./types";

const TASK_STATES: TaskState[] = ["todo", "wip", "blocked", "done", "validated"];

export interface TaskFiltersProps {
  /** Current filter values */
  filters: TaskFiltersType;
  /** Available sessions for dropdown */
  sessions: Session[];
  /** Callback when any filter changes */
  onFiltersChange: (filters: Partial<TaskFiltersType>) => void;
}

/**
 * TaskFilters provides filter controls for the tasks view.
 *
 * Features:
 * - Search input for text search
 * - State dropdown filter
 * - Session dropdown filter (when sessions provided)
 * - Accessible labels on all controls
 */
export function TaskFilters({
  filters,
  sessions,
  onFiltersChange,
}: TaskFiltersProps) {
  const handleSearchChange = (event: ChangeEvent<HTMLInputElement>) => {
    onFiltersChange({ search: event.target.value });
  };

  const handleStateChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    onFiltersChange({ state: value ? (value as TaskState) : undefined });
  };

  const handleSessionChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    onFiltersChange({ sessionId: value || undefined });
  };

  return (
    <div className="flex flex-wrap gap-4">
      {/* Search input */}
      <div className="flex flex-col">
        <label className="sr-only" htmlFor="task-search">
          Search tasks
        </label>
        <input
          className="h-9 w-64 rounded-md border border-gray-300 px-3 text-sm placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          id="task-search"
          onChange={handleSearchChange}
          placeholder="Search tasks..."
          type="text"
          value={filters.search || ""}
        />
      </div>

      {/* State filter */}
      <div className="flex flex-col">
        <label className="sr-only" htmlFor="state-filter">
          Filter by state
        </label>
        <select
          aria-label="Filter by state"
          className="h-9 rounded-md border border-gray-300 bg-white px-3 pr-8 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          id="state-filter"
          onChange={handleStateChange}
          value={filters.state || ""}
        >
          <option value="">All states</option>
          {TASK_STATES.map((state) => (
            <option key={state} value={state}>
              {state.charAt(0).toUpperCase() + state.slice(1)}
            </option>
          ))}
        </select>
      </div>

      {/* Session filter - always show, with "Unscoped" option for tasks without session */}
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
          <option value="none">Unscoped (no session)</option>
          {sessions.map((session) => (
            <option key={session.sessionId} value={session.sessionId}>
              {session.name || session.sessionId}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
