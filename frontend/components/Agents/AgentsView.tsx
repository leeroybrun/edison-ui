"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";

import { AgentCard } from "./AgentCard";
import type { TrackingRun, RunType, AgentFilters } from "./types";

export interface AgentsViewProps {
  /** Runs to display */
  runs: TrackingRun[];
  /** Error message if loading failed */
  error?: string;
  /** Whether data is loading */
  isLoading?: boolean;
  /** Callback for refresh action */
  onRefresh?: () => void;
  /** Auto-refresh interval in milliseconds (default: 10000) */
  autoRefreshInterval?: number;
}

/**
 * AgentsView is the main component for displaying active agents/runs.
 *
 * Features:
 * - List of agent cards with status indicators
 * - Filtering by session ID and run type
 * - Auto-refresh capability
 * - URL-based state management
 */
export function AgentsView({
  runs,
  error,
  isLoading,
  onRefresh,
  autoRefreshInterval = 10000,
}: AgentsViewProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // Get initial values from URL
  const urlSessionId = searchParams.get("sessionId");
  const urlType = searchParams.get("type") as RunType | null;

  const [filters, setFilters] = useState<AgentFilters>({
    sessionId: urlSessionId || undefined,
    type: urlType || undefined,
  });
  const [autoRefresh, setAutoRefresh] = useState(false);

  // Update URL when filters change
  const updateUrl = useCallback(
    (newFilters: AgentFilters) => {
      const params = new URLSearchParams();
      if (newFilters.sessionId) params.set("sessionId", newFilters.sessionId);
      if (newFilters.type) params.set("type", newFilters.type);

      const queryString = params.toString();
      router.push(queryString ? `${pathname}?${queryString}` : pathname);
    },
    [router, pathname],
  );

  // Handle filter changes
  const handleSessionFilterChange = useCallback(
    (event: React.ChangeEvent<HTMLSelectElement>) => {
      const value = event.target.value || undefined;
      const newFilters = { ...filters, sessionId: value };
      setFilters(newFilters);
      updateUrl(newFilters);
    },
    [filters, updateUrl],
  );

  const handleTypeFilterChange = useCallback(
    (event: React.ChangeEvent<HTMLSelectElement>) => {
      const value = (event.target.value || undefined) as RunType | undefined;
      const newFilters = { ...filters, type: value };
      setFilters(newFilters);
      updateUrl(newFilters);
    },
    [filters, updateUrl],
  );

  // Get unique session IDs for filter dropdown
  const sessionIds = useMemo(() => {
    const ids = new Set<string>();
    runs.forEach((run) => {
      if (run.sessionId) {
        ids.add(run.sessionId);
      }
    });
    return Array.from(ids).sort();
  }, [runs]);

  // Filter runs based on current filters
  const filteredRuns = useMemo(() => {
    return runs.filter((run) => {
      // Session filter
      if (filters.sessionId && run.sessionId !== filters.sessionId) {
        return false;
      }

      // Type filter
      if (filters.type && run.type !== filters.type) {
        return false;
      }

      return true;
    });
  }, [runs, filters]);

  // Auto-refresh effect
  useEffect(() => {
    if (!autoRefresh || !onRefresh) return;

    const intervalId = setInterval(() => {
      onRefresh();
    }, autoRefreshInterval);

    return () => clearInterval(intervalId);
  }, [autoRefresh, onRefresh, autoRefreshInterval]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <span className="text-gray-500">Loading agents...</span>
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
      {/* Header with filters and controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* Filter controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Session filter */}
          <div className="flex items-center gap-2">
            <label
              className="text-sm font-medium text-gray-700"
              htmlFor="session-filter"
            >
              Session
            </label>
            <select
              className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              id="session-filter"
              onChange={handleSessionFilterChange}
              value={filters.sessionId || ""}
            >
              <option value="">All Sessions</option>
              {sessionIds.map((id) => (
                <option key={id} value={id}>
                  {id}
                </option>
              ))}
            </select>
          </div>

          {/* Type filter */}
          <div className="flex items-center gap-2">
            <label
              className="text-sm font-medium text-gray-700"
              htmlFor="type-filter"
            >
              Type
            </label>
            <select
              className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              id="type-filter"
              onChange={handleTypeFilterChange}
              value={filters.type || ""}
            >
              <option value="">All Types</option>
              <option value="implementation">Implementation</option>
              <option value="validation">Validation</option>
              <option value="orchestrator">Orchestrator</option>
            </select>
          </div>
        </div>

        {/* Right side controls */}
        <div className="flex items-center gap-4">
          {/* Count indicator */}
          <span className="text-sm text-gray-600">
            {filteredRuns.length} agents
          </span>

          {/* Auto-refresh toggle */}
          <label className="flex cursor-pointer items-center gap-2">
            <input
              aria-label="Auto-refresh"
              checked={autoRefresh}
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              onChange={(e) => setAutoRefresh(e.target.checked)}
              type="checkbox"
            />
            <span className="text-sm text-gray-700">Auto-refresh</span>
          </label>

          {/* Manual refresh button */}
          {onRefresh && (
            <button
              className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
              onClick={onRefresh}
              type="button"
            >
              Refresh
            </button>
          )}
        </div>
      </div>

      {/* Agents region */}
      <section aria-label="Agents" role="region">
        {/* Empty state */}
        {runs.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-lg border bg-white py-12">
            <svg
              aria-hidden="true"
              className="mb-4 h-12 w-12 text-gray-300"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.5}
              viewBox="0 0 24 24"
            >
              <path
                d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <p className="text-gray-500">No active agents found</p>
          </div>
        )}

        {/* No matches state */}
        {runs.length > 0 && filteredRuns.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-lg border bg-white py-12">
            <p className="text-gray-500">No agents match your filters</p>
          </div>
        )}

        {/* Agent cards grid */}
        {filteredRuns.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
            {filteredRuns.map((run) => (
              <AgentCard key={run.runId} run={run} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
