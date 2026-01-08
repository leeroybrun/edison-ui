"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import {
  ActivityTimeline,
  AuditEventList,
  AuditFilters,
  type ActivityItem,
  type AuditEvent,
  type AuditFiltersState,
  type Session,
  type TaskRef,
} from "../../../../components/Activity";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ActivityPageClientProps {
  /** Initial activity items */
  initialActivityItems: ActivityItem[];
  /** Initial audit items */
  initialAuditItems: AuditEvent[];
  /** Initial hasMore state */
  hasMore: boolean;
  /** Project ID */
  projectId: string;
  /** Available sessions for filter */
  sessions: Session[];
  /** Available tasks for filter */
  tasks: TaskRef[];
  /** Initial filter values */
  initialFilters: AuditFiltersState;
  /** Initial view mode */
  initialView: "activity" | "audit";
  /** Error message if any */
  error?: string;
}

/**
 * ActivityPageClient is the client-side component for the activity page.
 *
 * Features:
 * - Toggle between activity and raw audit views
 * - Filter controls
 * - Infinite scroll / Load more
 * - URL state sync
 */
export function ActivityPageClient({
  initialActivityItems,
  initialAuditItems,
  hasMore: initialHasMore,
  projectId,
  sessions,
  tasks,
  initialFilters,
  initialView,
  error,
}: ActivityPageClientProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [view, setView] = useState<"activity" | "audit">(initialView);
  const [activityItems, setActivityItems] =
    useState<ActivityItem[]>(initialActivityItems);
  const [auditItems, setAuditItems] = useState<AuditEvent[]>(initialAuditItems);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(initialHasMore);
  const [filters, setFilters] = useState<AuditFiltersState>(initialFilters);
  const [offset, setOffset] = useState(
    initialView === "audit"
      ? initialAuditItems.length
      : initialActivityItems.length,
  );

  // Track if this is the initial mount to avoid double-fetching
  const isInitialMount = useRef(true);

  // Sync state from URL changes (browser back/forward)
  useEffect(() => {
    // Skip on initial mount since we have server-provided data
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }

    // Read current URL state
    const urlView =
      searchParams.get("view") === "audit" ? "audit" : "activity";
    const urlFilters: AuditFiltersState = {
      sessionId: searchParams.get("sessionId") || undefined,
      taskId: searchParams.get("taskId") || undefined,
      eventType: searchParams.get("eventType") || undefined,
      since: searchParams.get("since") || undefined,
    };

    // Update state if URL changed
    const viewChanged = urlView !== view;
    const filtersChanged =
      urlFilters.sessionId !== filters.sessionId ||
      urlFilters.taskId !== filters.taskId ||
      urlFilters.eventType !== filters.eventType ||
      urlFilters.since !== filters.since;

    if (viewChanged || filtersChanged) {
      setView(urlView);
      setFilters(urlFilters);
      setOffset(0);
      fetchData(urlFilters, urlView, 0, false);
    }
  }, [searchParams]); // eslint-disable-line react-hooks/exhaustive-deps

  const updateURL = useCallback(
    (newFilters: AuditFiltersState, newView: "activity" | "audit") => {
      const params = new URLSearchParams();
      if (newFilters.sessionId) params.set("sessionId", newFilters.sessionId);
      if (newFilters.taskId) params.set("taskId", newFilters.taskId);
      if (newFilters.eventType) params.set("eventType", newFilters.eventType);
      if (newFilters.since) params.set("since", newFilters.since);
      if (newView !== "activity") params.set("view", newView);

      const newURL = `/projects/${projectId}/activity${params.toString() ? `?${params.toString()}` : ""}`;
      router.push(newURL, { scroll: false });
    },
    [projectId, router],
  );

  const fetchData = useCallback(
    async (
      currentFilters: AuditFiltersState,
      currentView: "activity" | "audit",
      fetchOffset: number = 0,
      append: boolean = false,
    ) => {
      setLoading(true);

      try {
        const params = new URLSearchParams();
        if (currentFilters.sessionId)
          params.set("sessionId", currentFilters.sessionId);
        if (currentFilters.taskId) params.set("taskId", currentFilters.taskId);
        if (currentFilters.eventType)
          params.set("eventType", currentFilters.eventType);
        if (currentFilters.since) params.set("since", currentFilters.since);
        params.set("limit", "50");
        params.set("offset", String(fetchOffset));

        const endpoint = currentView === "audit" ? "audit" : "activity";
        const url = `${API_BASE_URL}/api/v1/projects/${projectId}/${endpoint}?${params.toString()}`;

        const response = await fetch(url, { cache: "no-store" });

        if (!response.ok) {
          throw new Error(`Failed to fetch ${endpoint}`);
        }

        const data = await response.json();

        if (currentView === "audit") {
          if (append) {
            setAuditItems((prev) => [...prev, ...data.items]);
          } else {
            setAuditItems(data.items);
          }
        } else {
          if (append) {
            setActivityItems((prev) => [...prev, ...data.items]);
          } else {
            setActivityItems(data.items);
          }
        }
        setHasMore(data.hasMore);
        setOffset(fetchOffset + data.items.length);
      } catch (err) {
        console.error("Error fetching data:", err);
      } finally {
        setLoading(false);
      }
    },
    [projectId],
  );

  const handleFiltersChange = useCallback(
    (newFilters: Partial<AuditFiltersState>) => {
      const updatedFilters = { ...filters, ...newFilters };
      setFilters(updatedFilters);
      setOffset(0);
      updateURL(updatedFilters, view);
      fetchData(updatedFilters, view, 0, false);
    },
    [filters, view, updateURL, fetchData],
  );

  const handleViewChange = useCallback(
    (newView: "activity" | "audit") => {
      setView(newView);
      setOffset(0);
      updateURL(filters, newView);
      fetchData(filters, newView, 0, false);
    },
    [filters, updateURL, fetchData],
  );

  const handleLoadMore = useCallback(async () => {
    await fetchData(filters, view, offset, true);
  }, [filters, view, offset, fetchData]);

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
        <p className="font-medium">Error loading activity</p>
        <p className="text-sm">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* View toggle and filters */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        {/* View toggle */}
        <div className="flex rounded-lg border bg-gray-100 p-1">
          <button
            className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              view === "activity"
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-600 hover:text-gray-900"
            }`}
            onClick={() => handleViewChange("activity")}
            type="button"
          >
            Activity
          </button>
          <button
            className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              view === "audit"
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-600 hover:text-gray-900"
            }`}
            onClick={() => handleViewChange("audit")}
            type="button"
          >
            Raw Audit
          </button>
        </div>

        {/* Filters */}
        <AuditFilters
          filters={filters}
          onChange={handleFiltersChange}
          sessions={sessions}
          tasks={tasks}
        />
      </div>

      {/* Content */}
      {view === "activity" ? (
        <ActivityTimeline
          hasMore={hasMore}
          items={activityItems}
          loading={loading}
          onLoadMore={handleLoadMore}
        />
      ) : (
        <AuditEventList
          hasMore={hasMore}
          items={auditItems}
          loading={loading}
          onLoadMore={handleLoadMore}
          showRaw={false}
        />
      )}
    </div>
  );
}
