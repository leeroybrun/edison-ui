"use client";

import type { ChangeEvent } from "react";

import type { Session, QAFilters as QAFiltersType, QAState } from "./types";

const QA_STATES: QAState[] = ["waiting", "todo", "wip", "done", "validated"];
const QA_VERDICTS = ["passed", "rejected", "in_progress"] as const;

export interface QAFiltersProps {
  /** Current filter values */
  filters: QAFiltersType;
  /** Available sessions for dropdown */
  sessions: Session[];
  /** Callback when any filter changes */
  onFiltersChange: (filters: Partial<QAFiltersType>) => void;
  /** When true, hides the session filter dropdown */
  hideSessionFilter?: boolean;
}

/**
 * QAFilters provides filter controls for the QA view.
 *
 * Features:
 * - Search input for text search
 * - State dropdown filter
 * - Verdict dropdown filter
 * - Validator text input filter
 * - Session dropdown filter (when sessions provided)
 * - Accessible labels on all controls
 */
export function QAFilters({
  filters,
  sessions,
  onFiltersChange,
  hideSessionFilter = false,
}: QAFiltersProps) {
  const handleSearchChange = (event: ChangeEvent<HTMLInputElement>) => {
    onFiltersChange({ search: event.target.value });
  };

  const handleStateChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    onFiltersChange({ state: value ? (value as QAState) : undefined });
  };

  const handleVerdictChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    onFiltersChange({ verdict: value || undefined });
  };

  const handleValidatorChange = (event: ChangeEvent<HTMLInputElement>) => {
    onFiltersChange({ validator: event.target.value || undefined });
  };

  const handleSessionChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    onFiltersChange({ sessionId: value || undefined });
  };

  return (
    <div className="flex flex-wrap gap-4">
      {/* Search input */}
      <div className="flex flex-col">
        <label className="sr-only" htmlFor="qa-search">
          Search QA records
        </label>
        <input
          className="h-9 w-48 rounded-md border border-gray-300 px-3 text-sm placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          id="qa-search"
          onChange={handleSearchChange}
          placeholder="Search QA..."
          type="text"
          value={filters.search || ""}
        />
      </div>

      {/* State filter */}
      <div className="flex flex-col">
        <label className="sr-only" htmlFor="qa-state-filter">
          Filter by state
        </label>
        <select
          aria-label="Filter by state"
          className="h-9 rounded-md border border-gray-300 bg-white px-3 pr-8 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          id="qa-state-filter"
          onChange={handleStateChange}
          value={filters.state || ""}
        >
          <option value="">All states</option>
          {QA_STATES.map((state) => (
            <option key={state} value={state}>
              {state.charAt(0).toUpperCase() + state.slice(1)}
            </option>
          ))}
        </select>
      </div>

      {/* Verdict filter */}
      <div className="flex flex-col">
        <label className="sr-only" htmlFor="qa-verdict-filter">
          Filter by verdict
        </label>
        <select
          aria-label="Filter by verdict"
          className="h-9 rounded-md border border-gray-300 bg-white px-3 pr-8 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          id="qa-verdict-filter"
          onChange={handleVerdictChange}
          value={filters.verdict || ""}
        >
          <option value="">All verdicts</option>
          {QA_VERDICTS.map((verdict) => (
            <option key={verdict} value={verdict}>
              {verdict.charAt(0).toUpperCase() +
                verdict.slice(1).replace("_", " ")}
            </option>
          ))}
        </select>
      </div>

      {/* Validator filter */}
      <div className="flex flex-col">
        <label className="sr-only" htmlFor="qa-validator-filter">
          Filter by validator
        </label>
        <input
          aria-label="Filter by validator"
          className="h-9 w-40 rounded-md border border-gray-300 px-3 text-sm placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          id="qa-validator-filter"
          onChange={handleValidatorChange}
          placeholder="Validator..."
          type="text"
          value={filters.validator || ""}
        />
      </div>

      {/* Session filter - conditionally rendered based on hideSessionFilter prop */}
      {!hideSessionFilter && (
        <div className="flex flex-col">
          <label className="sr-only" htmlFor="qa-session-filter">
            Filter by session
          </label>
          <select
            aria-label="Filter by session"
            className="h-9 rounded-md border border-gray-300 bg-white px-3 pr-8 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            id="qa-session-filter"
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
      )}
    </div>
  );
}
