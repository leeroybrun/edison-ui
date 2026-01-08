"use client";

import { useState, useEffect, useCallback } from "react";

import { ActivityTimeline } from "./ActivityTimeline";
import type { ActivityItem, ActivityResponse } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface EntityAuditPanelProps {
  /** Type of entity to show audit for */
  entityType: "task" | "session";
  /** ID of the entity */
  entityId: string;
  /** Project ID */
  projectId: string;
}

/**
 * EntityAuditPanel shows audit history for a specific entity (task or session).
 *
 * Features:
 * - Fetches activity filtered by entity
 * - Shows timeline of changes to this entity
 * - Collapsible panel
 * - Loading and error states
 */
export function EntityAuditPanel({
  entityType,
  entityId,
  projectId,
}: EntityAuditPanelProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [items, setItems] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [offset, setOffset] = useState(0);

  const fetchActivity = useCallback(
    async (fetchOffset: number = 0, append: boolean = false) => {
      setLoading(true);
      setError(null);

      try {
        const params = new URLSearchParams();
        if (entityType === "task") {
          params.set("taskId", entityId);
        } else {
          params.set("sessionId", entityId);
        }
        params.set("limit", "50");
        params.set("offset", String(fetchOffset));

        const response = await fetch(
          `${API_BASE_URL}/api/v1/projects/${projectId}/activity?${params.toString()}`,
          { cache: "no-store" },
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch activity: ${response.statusText}`);
        }

        const data: ActivityResponse = await response.json();
        if (append) {
          setItems((prev) => [...prev, ...data.items]);
        } else {
          setItems(data.items);
        }
        setHasMore(data.hasMore);
        setOffset(fetchOffset + data.items.length);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to fetch activity",
        );
      } finally {
        setLoading(false);
      }
    },
    [entityType, entityId, projectId],
  );

  useEffect(() => {
    setOffset(0);
    fetchActivity(0, false);
  }, [fetchActivity]);

  const handleLoadMore = useCallback(async () => {
    await fetchActivity(offset, true);
  }, [fetchActivity, offset]);

  const toggleExpanded = () => {
    setIsExpanded((prev) => !prev);
  };

  const entityLabel = entityType === "task" ? entityId : entityId;
  const panelTitle = `${entityType === "task" ? "Task" : "Session"} ${entityLabel} Activity`;

  return (
    <div className="rounded-lg border bg-white shadow-sm">
      {/* Panel header */}
      <div className="flex items-center justify-between border-b px-4 py-3">
        <h3 className="text-sm font-medium text-gray-900">{panelTitle}</h3>
        <button
          aria-expanded={isExpanded}
          aria-label={isExpanded ? "Collapse panel" : "Expand panel"}
          className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          onClick={toggleExpanded}
          type="button"
        >
          <svg
            aria-hidden="true"
            className={`h-5 w-5 transition-transform ${isExpanded ? "rotate-180" : ""}`}
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

      {/* Panel content */}
      {isExpanded && (
        <div className="p-4">
          {error ? (
            <div className="flex flex-col items-center justify-center py-8 text-red-500">
              <svg
                aria-hidden="true"
                className="mb-2 h-8 w-8"
                fill="none"
                stroke="currentColor"
                strokeWidth={1.5}
                viewBox="0 0 24 24"
              >
                <path
                  d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <p className="text-sm">Error loading activity</p>
              <p className="text-xs text-gray-500">{error}</p>
            </div>
          ) : (
            <ActivityTimeline
              hasMore={hasMore}
              items={items}
              loading={loading}
              onLoadMore={handleLoadMore}
            />
          )}
        </div>
      )}
    </div>
  );
}
