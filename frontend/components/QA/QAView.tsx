"use client";

import { useCallback, useMemo, useState } from "react";
import type { ChangeEvent } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";

import type { QARecord, Session, QAState, ViewMode, QAFilters } from "./types";

/**
 * State badge color mappings
 */
const STATE_COLORS: Record<QAState, string> = {
  waiting: "bg-gray-100 text-gray-800",
  todo: "bg-yellow-100 text-yellow-800",
  wip: "bg-blue-100 text-blue-800",
  done: "bg-green-100 text-green-800",
  validated: "bg-purple-100 text-purple-800",
};

/**
 * Verdict badge color mappings
 */
const VERDICT_COLORS: Record<string, string> = {
  passed: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  in_progress: "bg-yellow-100 text-yellow-800",
};

/**
 * Board column states (ordered)
 */
const BOARD_COLUMNS: QAState[] = [
  "waiting",
  "todo",
  "wip",
  "done",
  "validated",
];

export interface QAViewProps {
  /** QA records to display */
  qaRecords: QARecord[];
  /** Available sessions for filtering */
  sessions: Session[];
  /** Initial view mode */
  initialView?: ViewMode;
  /** Error message if loading failed */
  error?: string;
  /** Whether data is loading */
  isLoading?: boolean;
  /**
   * When provided, locks the view to a specific session.
   * The session filter dropdown is hidden and records are pre-filtered.
   */
  lockedSessionId?: string;
}

/**
 * Format date string for display
 */
function formatDate(isoDate: string): string {
  const date = new Date(isoDate);
  return date.toLocaleDateString();
}

/**
 * QAView is the main component for displaying QA records.
 *
 * Features:
 * - Two view modes: list, board
 * - Filtering by state, verdict, session, validator, and search text
 * - URL-based state management
 * - Accessible region with proper roles
 * - Locked session mode for session detail pages
 */
export function QAView({
  qaRecords,
  sessions,
  initialView = "list",
  error,
  isLoading,
  lockedSessionId,
}: QAViewProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // Get initial values from URL
  const urlView = (searchParams.get("view") as ViewMode) || initialView;
  const urlState = searchParams.get("state") as QAState | null;
  const urlVerdict = searchParams.get("verdict");
  const urlSession = searchParams.get("sessionId");
  const urlValidator = searchParams.get("validator");
  const urlSearch = searchParams.get("search");

  const [viewMode, setViewMode] = useState<ViewMode>(urlView);
  const [filters, setFilters] = useState<QAFilters>({
    state: urlState || undefined,
    verdict: urlVerdict || undefined,
    // If lockedSessionId is provided, use it and ignore URL param
    sessionId: lockedSessionId || urlSession || undefined,
    validator: urlValidator || undefined,
    search: urlSearch || undefined,
  });

  // Update URL when view or filters change
  const updateUrl = useCallback(
    (newView: ViewMode, newFilters: QAFilters) => {
      const params = new URLSearchParams();
      if (newView !== "list") params.set("view", newView);
      if (newFilters.state) params.set("state", newFilters.state);
      if (newFilters.verdict) params.set("verdict", newFilters.verdict);
      // Don't add sessionId to URL if it's locked (managed by page context)
      if (newFilters.sessionId && !lockedSessionId) {
        params.set("sessionId", newFilters.sessionId);
      }
      if (newFilters.validator) params.set("validator", newFilters.validator);
      if (newFilters.search) params.set("search", newFilters.search);

      const queryString = params.toString();
      router.push(queryString ? `${pathname}?${queryString}` : pathname);
    },
    [router, pathname, lockedSessionId],
  );

  // Handle view mode change
  const handleViewChange = useCallback(
    (newView: ViewMode) => {
      setViewMode(newView);
      updateUrl(newView, filters);
    },
    [filters, updateUrl],
  );

  // Handle filter changes
  const handleFiltersChange = useCallback(
    (newFilters: Partial<QAFilters>) => {
      const updatedFilters = { ...filters, ...newFilters };
      setFilters(updatedFilters);
      updateUrl(viewMode, updatedFilters);
    },
    [filters, viewMode, updateUrl],
  );

  // Handle individual filter input changes
  const handleSearchChange = (event: ChangeEvent<HTMLInputElement>) => {
    handleFiltersChange({ search: event.target.value || undefined });
  };

  const handleStateChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    handleFiltersChange({ state: value ? (value as QAState) : undefined });
  };

  const handleVerdictChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    handleFiltersChange({ verdict: value || undefined });
  };

  const handleSessionChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    handleFiltersChange({ sessionId: value || undefined });
  };

  const handleValidatorChange = (event: ChangeEvent<HTMLInputElement>) => {
    handleFiltersChange({ validator: event.target.value || undefined });
  };

  // Filter QA records based on current filters
  const filteredRecords = useMemo(() => {
    return qaRecords.filter((record) => {
      // State filter
      if (filters.state && record.state !== filters.state) {
        return false;
      }

      // Verdict filter
      if (filters.verdict && record.verdict !== filters.verdict) {
        return false;
      }

      // Session filter - "none" means unscoped records (sessionId is null)
      if (filters.sessionId) {
        if (filters.sessionId === "none") {
          // Filter for unscoped records (no session)
          if (record.sessionId !== null) {
            return false;
          }
        } else if (record.sessionId !== filters.sessionId) {
          return false;
        }
      }

      // Validator filter
      if (filters.validator) {
        const validatorLower = filters.validator.toLowerCase();
        const matchesValidator = record.validators.some((v) =>
          v.toLowerCase().includes(validatorLower),
        );
        if (!matchesValidator) {
          return false;
        }
      }

      // Search filter
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        const matchesQaId = record.qaId.toLowerCase().includes(searchLower);
        const matchesTaskId = record.taskId.toLowerCase().includes(searchLower);
        if (!matchesQaId && !matchesTaskId) {
          return false;
        }
      }

      return true;
    });
  }, [qaRecords, filters]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <span className="text-gray-500">Loading QA records...</span>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div
        className="rounded-lg border border-red-200 bg-red-50 p-4"
        role="alert"
      >
        <p className="text-red-800">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with view toggle and filters */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* View toggle */}
        <div className="flex rounded-lg border bg-white p-1" role="group">
          {(["list", "board"] as const).map((mode) => (
            <button
              key={mode}
              aria-pressed={viewMode === mode}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                viewMode === mode
                  ? "bg-blue-100 text-blue-700"
                  : "text-gray-600 hover:bg-gray-100"
              }`}
              onClick={() => handleViewChange(mode)}
              type="button"
            >
              {mode.charAt(0).toUpperCase() + mode.slice(1)}
            </button>
          ))}
        </div>

        {/* Locked session indicator */}
        {lockedSessionId && (
          <div
            className="flex items-center gap-2 rounded-md bg-blue-50 px-3 py-1.5"
            data-testid="locked-session-indicator"
          >
            <svg
              className="h-4 w-4 text-blue-600"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              viewBox="0 0 24 24"
            >
              <path
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <span className="text-sm font-medium text-blue-700">
              Session: {lockedSessionId}
            </span>
          </div>
        )}

        {/* Filters */}
        <div className="flex flex-wrap gap-4">
          {/* Search input */}
          <div className="flex flex-col">
            <label className="sr-only" htmlFor="qa-search">
              Search QA records
            </label>
            <input
              className="h-9 w-64 rounded-md border border-gray-300 px-3 text-sm placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              id="qa-search"
              onChange={handleSearchChange}
              placeholder="Search QA records..."
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
              {BOARD_COLUMNS.map((state) => (
                <option key={state} value={state}>
                  {state.charAt(0).toUpperCase() + state.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* Verdict filter */}
          <div className="flex flex-col">
            <label className="sr-only" htmlFor="verdict-filter">
              Filter by verdict
            </label>
            <select
              aria-label="Filter by verdict"
              className="h-9 rounded-md border border-gray-300 bg-white px-3 pr-8 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              id="verdict-filter"
              onChange={handleVerdictChange}
              value={filters.verdict || ""}
            >
              <option value="">All verdicts</option>
              <option value="passed">Passed</option>
              <option value="rejected">Rejected</option>
              <option value="in_progress">In Progress</option>
            </select>
          </div>

          {/* Session filter - conditionally rendered based on lockedSessionId */}
          {!lockedSessionId && (
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
          )}

          {/* Validator filter */}
          <div className="flex flex-col">
            <label className="sr-only" htmlFor="validator-filter">
              Filter by validator
            </label>
            <input
              aria-label="Filter by validator"
              className="h-9 w-40 rounded-md border border-gray-300 px-3 text-sm placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              id="validator-filter"
              onChange={handleValidatorChange}
              placeholder="Validator..."
              type="text"
              value={filters.validator || ""}
            />
          </div>
        </div>
      </div>

      {/* QA records region */}
      <section aria-label="QA Records" role="region" tabIndex={0}>
        {/* Empty state */}
        {qaRecords.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-lg border bg-white py-12">
            <p className="text-gray-500">No QA records found</p>
          </div>
        )}

        {/* No matches state */}
        {qaRecords.length > 0 && filteredRecords.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-lg border bg-white py-12">
            <p className="text-gray-500">No QA records match your filters</p>
          </div>
        )}

        {/* List View */}
        {viewMode === "list" && filteredRecords.length > 0 && (
          <div className="overflow-hidden rounded-lg border bg-white">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                    scope="col"
                  >
                    QA ID
                  </th>
                  <th
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                    scope="col"
                  >
                    Task
                  </th>
                  <th
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                    scope="col"
                  >
                    State
                  </th>
                  <th
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                    scope="col"
                  >
                    Verdict
                  </th>
                  <th
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                    scope="col"
                  >
                    Round
                  </th>
                  <th
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                    scope="col"
                  >
                    Validators
                  </th>
                  <th
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                    scope="col"
                  >
                    Updated
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {filteredRecords.map((record) => (
                  <tr className="hover:bg-gray-50" key={record.qaId}>
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-sm text-gray-900">
                      {record.qaId}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-sm text-gray-900">
                      {record.taskId}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${STATE_COLORS[record.state]}`}
                      >
                        {record.state}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">
                      {record.verdict ? (
                        <span
                          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${VERDICT_COLORS[record.verdict] || "bg-gray-100 text-gray-800"}`}
                        >
                          {record.verdict}
                        </span>
                      ) : (
                        <span className="text-sm text-gray-400">-</span>
                      )}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-900">
                      {record.round}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {record.validators.length > 0
                        ? record.validators.join(", ")
                        : "-"}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
                      {formatDate(record.updatedAt)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Board View */}
        {viewMode === "board" && filteredRecords.length > 0 && (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">
            {BOARD_COLUMNS.map((state) => {
              const columnRecords = filteredRecords.filter(
                (r) => r.state === state,
              );
              return (
                <div
                  className="rounded-lg border bg-gray-50 p-3"
                  data-column={state}
                  key={state}
                >
                  <h3 className="mb-3 text-sm font-semibold uppercase text-gray-700">
                    {state} ({columnRecords.length})
                  </h3>
                  <div className="space-y-2">
                    {columnRecords.map((record) => (
                      <div
                        className="rounded-lg border bg-white p-3 shadow-sm"
                        key={record.qaId}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-sm font-medium text-gray-900">
                            {record.qaId}
                          </span>
                          {record.verdict && (
                            <span
                              className={`rounded-full px-2 py-0.5 text-xs font-medium ${VERDICT_COLORS[record.verdict] || "bg-gray-100 text-gray-800"}`}
                            >
                              {record.verdict}
                            </span>
                          )}
                        </div>
                        <div className="mt-1 font-mono text-xs text-gray-500">
                          {record.taskId}
                        </div>
                        <div className="mt-2 text-xs text-gray-400">
                          Round {record.round}
                        </div>
                      </div>
                    ))}
                    {columnRecords.length === 0 && (
                      <p className="py-4 text-center text-sm text-gray-400">
                        No records
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
