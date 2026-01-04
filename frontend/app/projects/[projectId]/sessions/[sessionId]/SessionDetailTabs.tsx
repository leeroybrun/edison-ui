"use client";

import Link from "next/link";

export interface SessionDetailTabsProps {
  /** Currently active tab */
  activeTab: "tasks" | "qa";
  /** Project ID for URL generation */
  projectId: string;
  /** Session ID for URL generation */
  sessionId: string;
  /** Number of tasks in this session */
  taskCount: number;
  /** Number of QA records in this session */
  qaCount: number;
}

/**
 * Tab navigation component for session detail page.
 * Provides links to switch between Tasks and QA views.
 */
export function SessionDetailTabs({
  activeTab,
  projectId,
  sessionId,
  taskCount,
  qaCount,
}: SessionDetailTabsProps) {
  const baseUrl = `/projects/${projectId}/sessions/${sessionId}`;

  return (
    <nav aria-label="Session tabs" className="border-b border-gray-200">
      <ul className="-mb-px flex gap-4" role="tablist">
        <li role="presentation">
          <Link
            aria-selected={activeTab === "tasks"}
            className={`inline-flex items-center gap-2 border-b-2 px-1 py-3 text-sm font-medium transition-colors ${
              activeTab === "tasks"
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
            }`}
            href={baseUrl}
            role="tab"
          >
            Tasks
            <span
              className={`rounded-full px-2 py-0.5 text-xs ${
                activeTab === "tasks"
                  ? "bg-blue-100 text-blue-600"
                  : "bg-gray-100 text-gray-600"
              }`}
            >
              {taskCount}
            </span>
          </Link>
        </li>
        <li role="presentation">
          <Link
            aria-selected={activeTab === "qa"}
            className={`inline-flex items-center gap-2 border-b-2 px-1 py-3 text-sm font-medium transition-colors ${
              activeTab === "qa"
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
            }`}
            href={`${baseUrl}?tab=qa`}
            role="tab"
          >
            QA
            <span
              className={`rounded-full px-2 py-0.5 text-xs ${
                activeTab === "qa"
                  ? "bg-blue-100 text-blue-600"
                  : "bg-gray-100 text-gray-600"
              }`}
            >
              {qaCount}
            </span>
          </Link>
        </li>
      </ul>
    </nav>
  );
}
