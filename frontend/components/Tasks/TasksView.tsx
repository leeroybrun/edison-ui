"use client";

import { useCallback, useMemo, useState } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";

import { TaskCard } from "./TaskCard";
import { TaskFilters } from "./TaskFilters";
import type {
  Task,
  Session,
  TaskState,
  ViewMode,
  TaskFilters as TaskFiltersType,
} from "./types";

/**
 * State badge color mappings
 */
const STATE_COLORS: Record<TaskState, string> = {
  todo: "bg-gray-100 text-gray-800",
  wip: "bg-blue-100 text-blue-800",
  blocked: "bg-red-100 text-red-800",
  done: "bg-green-100 text-green-800",
  validated: "bg-purple-100 text-purple-800",
};

/**
 * Board column states (ordered)
 */
const BOARD_COLUMNS: TaskState[] = ["todo", "wip", "done", "validated"];

export interface TasksViewProps {
  /** Tasks to display */
  tasks: Task[];
  /** Available sessions for filtering */
  sessions: Session[];
  /** Initial view mode */
  initialView?: ViewMode;
  /** Error message if loading failed */
  error?: string;
  /** Whether data is loading */
  isLoading?: boolean;
}

/**
 * Format relative time from ISO date string
 */
function formatDate(isoDate: string): string {
  const date = new Date(isoDate);
  return date.toLocaleDateString();
}

/**
 * TasksView is the main component for displaying tasks.
 *
 * Features:
 * - Three view modes: list, board, tree
 * - Filtering by state, session, and search text
 * - URL-based state management
 * - Accessible region with proper roles
 */
export function TasksView({
  tasks,
  sessions,
  initialView = "list",
  error,
  isLoading,
}: TasksViewProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // Get initial values from URL
  const urlView = (searchParams.get("view") as ViewMode) || initialView;
  const urlState = searchParams.get("state") as TaskState | null;
  const urlSession = searchParams.get("sessionId");
  const urlSearch = searchParams.get("search");

  const [viewMode, setViewMode] = useState<ViewMode>(urlView);
  const [filters, setFilters] = useState<TaskFiltersType>({
    state: urlState || undefined,
    sessionId: urlSession || undefined,
    search: urlSearch || undefined,
  });

  // Track collapsed tree nodes
  const [collapsedNodes, setCollapsedNodes] = useState<Set<string>>(new Set());

  // Update URL when view or filters change
  const updateUrl = useCallback(
    (newView: ViewMode, newFilters: TaskFiltersType) => {
      const params = new URLSearchParams();
      if (newView !== "list") params.set("view", newView);
      if (newFilters.state) params.set("state", newFilters.state);
      if (newFilters.sessionId) params.set("sessionId", newFilters.sessionId);
      if (newFilters.search) params.set("search", newFilters.search);

      const queryString = params.toString();
      router.push(queryString ? `${pathname}?${queryString}` : pathname);
    },
    [router, pathname],
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
    (newFilters: Partial<TaskFiltersType>) => {
      const updatedFilters = { ...filters, ...newFilters };
      setFilters(updatedFilters);
      updateUrl(viewMode, updatedFilters);
    },
    [filters, viewMode, updateUrl],
  );

  // Filter tasks based on current filters
  const filteredTasks = useMemo(() => {
    return tasks.filter((task) => {
      // State filter
      if (filters.state && task.state !== filters.state) {
        return false;
      }

      // Session filter
      if (filters.sessionId && task.sessionId !== filters.sessionId) {
        return false;
      }

      // Search filter
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        const matchesTitle = task.title.toLowerCase().includes(searchLower);
        const matchesId = task.taskId.toLowerCase().includes(searchLower);
        if (!matchesTitle && !matchesId) {
          return false;
        }
      }

      return true;
    });
  }, [tasks, filters]);

  // Build task hierarchy for tree view
  const taskHierarchy = useMemo(() => {
    const taskMap = new Map<string, Task>();
    const children = new Map<string, Task[]>();

    // Build maps
    filteredTasks.forEach((task) => {
      taskMap.set(task.taskId, task);
      if (task.parentId) {
        const parentChildren = children.get(task.parentId) || [];
        parentChildren.push(task);
        children.set(task.parentId, parentChildren);
      }
    });

    // Get root tasks (no parent or parent not in filtered list)
    const rootTasks = filteredTasks.filter(
      (task) => !task.parentId || !taskMap.has(task.parentId),
    );

    return { rootTasks, children };
  }, [filteredTasks]);

  // Toggle tree node
  const toggleNode = useCallback((taskId: string) => {
    setCollapsedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(taskId)) {
        next.delete(taskId);
      } else {
        next.add(taskId);
      }
      return next;
    });
  }, []);

  // Render tree item recursively
  const renderTreeItem = (task: Task, depth: number = 0): React.ReactNode => {
    const children = taskHierarchy.children.get(task.taskId) || [];
    const hasChildren = children.length > 0;
    const isCollapsed = collapsedNodes.has(task.taskId);

    return (
      <div key={task.taskId} style={{ paddingLeft: depth * 24 }}>
        <div className="flex items-center gap-2 rounded py-2 hover:bg-gray-50">
          {/* Expand/collapse button */}
          {hasChildren ? (
            <button
              aria-label={`Toggle ${task.taskId} children`}
              className="flex h-6 w-6 items-center justify-center rounded text-gray-500 hover:bg-gray-200"
              onClick={() => toggleNode(task.taskId)}
              type="button"
            >
              <svg
                className={`h-4 w-4 transition-transform ${isCollapsed ? "" : "rotate-90"}`}
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
                viewBox="0 0 24 24"
              >
                <path
                  d="M9 5l7 7-7 7"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          ) : (
            <div className="h-6 w-6" />
          )}

          {/* Task info */}
          <span className="font-mono text-sm font-medium text-gray-900">
            {task.taskId}
          </span>
          <span className="flex-1 text-sm text-gray-700">{task.title}</span>
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATE_COLORS[task.state]}`}
          >
            {task.state}
          </span>
        </div>

        {/* Children */}
        {hasChildren && !isCollapsed && (
          <div>
            {children.map((child) => renderTreeItem(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <span className="text-gray-500">Loading tasks...</span>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4" role="alert">
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
          {(["list", "board", "tree"] as const).map((mode) => (
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

        {/* Filters */}
        <TaskFilters
          filters={filters}
          onFiltersChange={handleFiltersChange}
          sessions={sessions}
        />
      </div>

      {/* Tasks region */}
      <section aria-label="Tasks" role="region">
        {/* Empty state */}
        {tasks.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-lg border bg-white py-12">
            <p className="text-gray-500">No tasks found</p>
          </div>
        )}

        {/* No matches state */}
        {tasks.length > 0 && filteredTasks.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-lg border bg-white py-12">
            <p className="text-gray-500">No tasks match your filters</p>
          </div>
        )}

        {/* List View */}
        {viewMode === "list" && filteredTasks.length > 0 && (
          <div className="overflow-hidden rounded-lg border bg-white">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                    scope="col"
                  >
                    ID
                  </th>
                  <th
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                    scope="col"
                  >
                    Title
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
                    Session
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
                {filteredTasks.map((task) => (
                  <tr key={task.taskId} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-sm text-gray-900">
                      {task.taskId}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {task.title}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${STATE_COLORS[task.state]}`}
                      >
                        {task.state}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
                      {task.sessionId || "-"}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
                      {formatDate(task.updatedAt)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Board View */}
        {viewMode === "board" && filteredTasks.length > 0 && (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            {BOARD_COLUMNS.map((state) => {
              const columnTasks = filteredTasks.filter((t) => t.state === state);
              return (
                <div key={state} className="rounded-lg border bg-gray-50 p-3">
                  <h3 className="mb-3 text-sm font-semibold uppercase text-gray-700">
                    {state} ({columnTasks.length})
                  </h3>
                  <div className="space-y-2">
                    {columnTasks.map((task) => (
                      <TaskCard key={task.taskId} task={task} />
                    ))}
                    {columnTasks.length === 0 && (
                      <p className="py-4 text-center text-sm text-gray-400">
                        No tasks
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Tree View */}
        {viewMode === "tree" && filteredTasks.length > 0 && (
          <div className="rounded-lg border bg-white p-4">
            {taskHierarchy.rootTasks.map((task) => renderTreeItem(task))}
          </div>
        )}
      </section>
    </div>
  );
}
