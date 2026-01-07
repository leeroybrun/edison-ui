"use client";

import type { ReactNode } from "react";
import { useCallback, useState } from "react";
import { useParams, usePathname, useRouter } from "next/navigation";

import { ProjectSidebar } from "../../../components/ProjectSidebar";
import {
  KeyboardShortcutsProvider,
  useCommandPalette,
} from "../../../components/CommandPalette/KeyboardShortcuts";
import { CommandPalette } from "../../../components/CommandPalette/CommandPalette";
import type { Command } from "../../../components/CommandPalette/CommandPalette";
import { SearchDialog } from "../../../components/Search";
import type { SearchResult } from "../../../components/Search";

/**
 * Navigation items for mobile view
 */
const MOBILE_NAV_ITEMS = [
  { key: "dashboard", label: "Dashboard", pathSuffix: "" },
  { key: "sessions", label: "Sessions", pathSuffix: "/sessions" },
  { key: "tasks", label: "Tasks", pathSuffix: "/tasks" },
  { key: "qa", label: "QA", pathSuffix: "/qa" },
  { key: "agents", label: "Agents", pathSuffix: "/agents" },
  { key: "settings", label: "Settings", pathSuffix: "/settings" },
];

/**
 * CommandPaletteWrapper renders the command palette using context
 */
function CommandPaletteWrapper({
  projectId,
  onOpenSearch,
}: {
  projectId: string;
  onOpenSearch: () => void;
}) {
  const { isOpen, close } = useCommandPalette();
  const router = useRouter();

  // Define available commands for this project context
  const commands: Command[] = [
    {
      id: "search",
      label: "Search",
      shortcut: "/",
      category: "actions",
      action: () => {
        close();
        onOpenSearch();
      },
    },
    {
      id: "go-tasks",
      label: "Go to Tasks",
      shortcut: "g t",
      category: "navigation",
      action: () => {
        router.push(`/projects/${projectId}/tasks`);
      },
    },
    {
      id: "go-sessions",
      label: "Go to Sessions",
      shortcut: "g s",
      category: "navigation",
      action: () => {
        router.push(`/projects/${projectId}/sessions`);
      },
    },
    {
      id: "go-dashboard",
      label: "Go to Dashboard",
      category: "navigation",
      action: () => {
        router.push(`/projects/${projectId}`);
      },
    },
    {
      id: "go-qa",
      label: "Go to QA",
      category: "navigation",
      action: () => {
        router.push(`/projects/${projectId}/qa`);
      },
    },
    {
      id: "go-agents",
      label: "Go to Agents",
      category: "navigation",
      action: () => {
        router.push(`/projects/${projectId}/agents`);
      },
    },
    {
      id: "go-settings",
      label: "Go to Settings",
      category: "navigation",
      action: () => {
        router.push(`/projects/${projectId}/settings`);
      },
    },
  ];

  return <CommandPalette commands={commands} isOpen={isOpen} onClose={close} />;
}

/**
 * Determines the active nav item based on the current pathname
 */
function getActiveItem(pathname: string, projectId: string): string {
  const basePath = `/projects/${projectId}`;

  // Check each nav item from most specific to least specific
  if (pathname.startsWith(`${basePath}/settings`)) return "settings";
  if (pathname.startsWith(`${basePath}/agents`)) return "agents";
  if (pathname.startsWith(`${basePath}/qa`)) return "qa";
  if (pathname.startsWith(`${basePath}/tasks`)) return "tasks";
  if (pathname.startsWith(`${basePath}/sessions`)) return "sessions";

  // Default to dashboard for the base project path
  return "dashboard";
}

interface ProjectLayoutProps {
  children: ReactNode;
}

/**
 * ProjectLayout provides the shell for project-specific pages.
 * Implements FR-011: persistent sidebar navigation shell.
 *
 * Features:
 * - Persistent sidebar with project navigation (hidden on mobile)
 * - Mobile navigation bar (visible on small screens)
 * - Active state detection based on current route
 * - Responsive layout that works on all screen sizes
 * - Integrated search dialog (T075)
 */
export default function ProjectLayout({ children }: ProjectLayoutProps) {
  const params = useParams<{ projectId: string }>();
  const pathname = usePathname();
  const router = useRouter();
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  const projectId = params.projectId;
  // Future: fetch project name from GET /api/v1/projects/{projectId}
  // For now, display the projectId which is human-readable
  const projectName = projectId;
  const activeItem = getActiveItem(pathname, projectId);

  // Get API base URL from environment or default
  const apiBaseUrl =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  const handleOpenSearch = useCallback(() => {
    setIsSearchOpen(true);
  }, []);

  const handleCloseSearch = useCallback(() => {
    setIsSearchOpen(false);
  }, []);

  const handleSearchSelect = useCallback(
    (result: SearchResult) => {
      // Navigate based on result type
      if (result.type === "task" && result.taskId) {
        router.push(`/projects/${projectId}/tasks?taskId=${result.taskId}`);
      } else if (result.type === "session" && result.sessionId) {
        router.push(`/projects/${projectId}/sessions/${result.sessionId}`);
      } else if (result.type === "qa" && result.qaId) {
        router.push(`/projects/${projectId}/qa?qaId=${result.qaId}`);
      }
    },
    [router, projectId],
  );

  return (
    <KeyboardShortcutsProvider>
      {/* Command Palette - rendered at top level for portal positioning */}
      <CommandPaletteWrapper
        projectId={projectId}
        onOpenSearch={handleOpenSearch}
      />

      {/* Search Dialog (T075) */}
      <SearchDialog
        isOpen={isSearchOpen}
        onClose={handleCloseSearch}
        onSelect={handleSearchSelect}
        projectId={projectId}
        apiBaseUrl={apiBaseUrl}
      />

      <div className="flex h-full">
        {/* Desktop sidebar - hidden on mobile */}
        <div className="hidden md:block">
          <ProjectSidebar
            projectId={projectId}
            projectName={projectName}
            activeItem={activeItem}
          />
        </div>

        {/* Main content area */}
        <div className="flex flex-1 flex-col">
          {/* Mobile header - visible on small screens only */}
          <header className="flex h-14 items-center border-b px-4 md:hidden">
            <a
              className="mr-3 text-gray-500 hover:text-gray-700"
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
            </a>
            <span className="truncate font-semibold text-gray-900">
              {projectName}
            </span>
          </header>

          {/* Mobile navigation - visible on small screens only */}
          <nav
            aria-label="Mobile project navigation"
            className="flex gap-1 overflow-x-auto border-b px-4 py-2 md:hidden"
          >
            {MOBILE_NAV_ITEMS.map((item) => {
              const href =
                item.pathSuffix === ""
                  ? `/projects/${projectId}`
                  : `/projects/${projectId}${item.pathSuffix}`;
              const isActive = activeItem === item.key;

              return (
                <a
                  key={item.key}
                  aria-current={isActive ? "page" : undefined}
                  className={`whitespace-nowrap rounded px-3 py-1.5 text-sm font-medium ${
                    isActive
                      ? "bg-blue-50 text-blue-700"
                      : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                  }`}
                  href={href}
                >
                  {item.label}
                </a>
              );
            })}
          </nav>

          {/* Main content */}
          <main className="flex-1 overflow-auto p-4 md:p-6">{children}</main>
        </div>
      </div>
    </KeyboardShortcutsProvider>
  );
}
