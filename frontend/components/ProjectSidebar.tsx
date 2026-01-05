"use client";

import Link from "next/link";

/**
 * Navigation item configuration
 */
interface NavItem {
  key: string;
  label: string;
  icon: React.ReactNode;
}

/**
 * Project sidebar navigation items per spec US1
 */
const NAV_ITEMS: NavItem[] = [
  {
    key: "dashboard",
    label: "Dashboard",
    icon: (
      <svg
        className="h-5 w-5"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        viewBox="0 0 24 24"
      >
        <path
          d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
  {
    key: "sessions",
    label: "Sessions",
    icon: (
      <svg
        className="h-5 w-5"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        viewBox="0 0 24 24"
      >
        <path
          d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
  {
    key: "tasks",
    label: "Tasks",
    icon: (
      <svg
        className="h-5 w-5"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        viewBox="0 0 24 24"
      >
        <path
          d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
  {
    key: "qa",
    label: "QA",
    icon: (
      <svg
        className="h-5 w-5"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        viewBox="0 0 24 24"
      >
        <path
          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
  {
    key: "agents",
    label: "Agents",
    icon: (
      <svg
        className="h-5 w-5"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        viewBox="0 0 24 24"
      >
        <path
          d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
  {
    key: "settings",
    label: "Settings",
    icon: (
      <svg
        className="h-5 w-5"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        viewBox="0 0 24 24"
      >
        <path
          d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
];

export interface ProjectSidebarProps {
  /** Project identifier used for building navigation URLs */
  projectId: string;
  /** Display name of the project */
  projectName: string;
  /** Currently active navigation item key */
  activeItem?: string;
  /** Whether the sidebar is in collapsed state */
  collapsed?: boolean;
  /** Callback when collapsed state changes */
  onCollapsedChange?: (collapsed: boolean) => void;
}

/**
 * Helper to build navigation href for a nav item
 */
function buildHref(projectId: string, itemKey: string): string {
  if (itemKey === "dashboard") {
    return `/projects/${projectId}`;
  }
  return `/projects/${projectId}/${itemKey}`;
}

/**
 * ProjectSidebar provides project-scoped navigation within a project shell.
 * Implements FR-011: persistent sidebar navigation shell.
 *
 * Features:
 * - Displays project name and back link to projects list
 * - Shows navigation for Dashboard, Sessions, Tasks, QA, Agents, Settings
 * - Supports collapsed/expanded states for responsive layouts
 * - Keyboard accessible with proper ARIA attributes
 */
export function ProjectSidebar({
  projectId,
  projectName,
  activeItem,
  collapsed = false,
  onCollapsedChange,
}: ProjectSidebarProps) {
  const handleToggle = () => {
    onCollapsedChange?.(!collapsed);
  };

  return (
    <aside
      className={`flex h-full flex-col border-r bg-gray-50 font-sans transition-all duration-200 ${
        collapsed ? "w-16" : "w-64"
      }`}
      data-testid="project-sidebar"
    >
      {/* Header with project name and back link */}
      <div className="flex flex-col border-b px-4 py-3">
        {!collapsed && (
          <>
            <Link
              className="mb-1 text-xs text-gray-500 hover:text-gray-700"
              href="/"
            >
              &larr; Back to projects
            </Link>
            <span
              className="truncate font-semibold text-gray-900"
              title={projectName}
            >
              {projectName}
            </span>
          </>
        )}
        {collapsed && (
          <Link
            aria-label="Back to projects"
            className="flex h-8 w-8 items-center justify-center rounded text-gray-500 hover:bg-gray-100 hover:text-gray-700"
            href="/"
            title="Back to projects"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              viewBox="0 0 24 24"
            >
              <path
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </Link>
        )}
      </div>

      {/* Navigation links */}
      <nav
        aria-label="Project navigation"
        className="flex-1 overflow-y-auto p-2"
      >
        <ul className="space-y-1">
          {NAV_ITEMS.map((item) => {
            const href = buildHref(projectId, item.key);
            const isActive = activeItem === item.key;

            return (
              <li key={item.key}>
                <Link
                  aria-current={isActive ? "page" : undefined}
                  className={`flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-blue-50 text-blue-700"
                      : "text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                  } ${collapsed ? "justify-center" : "gap-3"}`}
                  href={href}
                  title={collapsed ? item.label : undefined}
                >
                  <span className="flex-shrink-0">{item.icon}</span>
                  {!collapsed && <span>{item.label}</span>}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Collapse toggle button at bottom */}
      <div className="border-t p-2">
        <button
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="flex w-full items-center justify-center rounded-md px-3 py-2 text-sm text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700"
          onClick={handleToggle}
          type="button"
        >
          {collapsed ? (
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              viewBox="0 0 24 24"
            >
              <path
                d="M13 5l7 7-7 7M5 5l7 7-7 7"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          ) : (
            <>
              <svg
                className="h-5 w-5"
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
                viewBox="0 0 24 24"
              >
                <path
                  d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <span className="ml-2">Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
