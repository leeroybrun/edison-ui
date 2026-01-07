"use client";

import Link from "next/link";

export type SessionDetailTab = "tasks" | "qa" | "context" | "next";

export interface SessionDetailTabsProps {
  /** Currently active tab */
  activeTab: SessionDetailTab;
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
 * Provides links to switch between Tasks, QA, Context, and Next views.
 */
export function SessionDetailTabs({
  activeTab,
  projectId,
  sessionId,
  taskCount,
  qaCount,
}: SessionDetailTabsProps) {
  const baseUrl = `/projects/${projectId}/sessions/${sessionId}`;

  const getTabClasses = (tab: SessionDetailTab) =>
    `inline-flex items-center gap-2 border-b-2 px-1 py-3 text-sm font-medium transition-colors ${
      activeTab === tab
        ? "border-blue-500 text-blue-600"
        : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
    }`;

  const getBadgeClasses = (tab: SessionDetailTab) =>
    `rounded-full px-2 py-0.5 text-xs ${
      activeTab === tab ? "bg-blue-100 text-blue-600" : "bg-gray-100 text-gray-600"
    }`;

  return (
    <nav aria-label="Session tabs" className="border-b border-gray-200">
      <ul className="-mb-px flex gap-4" role="tablist">
        <li role="presentation">
          <Link
            aria-selected={activeTab === "tasks"}
            className={getTabClasses("tasks")}
            href={baseUrl}
            role="tab"
          >
            Tasks
            <span className={getBadgeClasses("tasks")}>{taskCount}</span>
          </Link>
        </li>
        <li role="presentation">
          <Link
            aria-selected={activeTab === "qa"}
            className={getTabClasses("qa")}
            href={`${baseUrl}?tab=qa`}
            role="tab"
          >
            QA
            <span className={getBadgeClasses("qa")}>{qaCount}</span>
          </Link>
        </li>
        <li role="presentation">
          <Link
            aria-selected={activeTab === "context"}
            className={getTabClasses("context")}
            href={`${baseUrl}?tab=context`}
            role="tab"
          >
            Context
          </Link>
        </li>
        <li role="presentation">
          <Link
            aria-selected={activeTab === "next"}
            className={getTabClasses("next")}
            href={`${baseUrl}?tab=next`}
            role="tab"
          >
            Next
          </Link>
        </li>
      </ul>
    </nav>
  );
}
