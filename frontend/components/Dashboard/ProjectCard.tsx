"use client";

import Link from "next/link";

import type { Project } from "./types";

interface ProjectCardProps {
  project: Project;
  onPin?: (projectId: string, pinned: boolean) => void;
}

/**
 * Format a date string to a relative time display.
 */
function formatRelativeTime(dateString: string | null): string {
  if (!dateString) {
    return "No recent activity";
  }

  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) {
    return "Just now";
  } else if (diffMins < 60) {
    return `${diffMins} minute${diffMins !== 1 ? "s" : ""} ago`;
  } else if (diffHours < 24) {
    return `${diffHours} hour${diffHours !== 1 ? "s" : ""} ago`;
  } else if (diffDays < 7) {
    return `${diffDays} day${diffDays !== 1 ? "s" : ""} ago`;
  } else {
    return date.toLocaleDateString();
  }
}

export function ProjectCard({ project, onPin }: ProjectCardProps) {
  const handlePinClick = () => {
    onPin?.(project.projectId, !project.pinned);
  };

  return (
    <article className="rounded-lg border bg-white p-4 shadow-sm transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="truncate text-lg font-semibold text-gray-900">
              {project.name}
            </h3>
            {project.hasGit && (
              <span
                aria-label="Git repository"
                className="text-gray-400"
                title="Git repository"
              >
                <svg
                  className="h-4 w-4"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
                </svg>
              </span>
            )}
            {project.errors.length > 0 && (
              <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800">
                {project.errors.length} error
                {project.errors.length !== 1 ? "s" : ""}
              </span>
            )}
          </div>
          <p className="mt-1 truncate text-sm text-gray-500">{project.path}</p>
        </div>

        <button
          aria-label={project.pinned ? "Unpin project" : "Pin project"}
          className={`ml-2 rounded p-1.5 transition-colors ${
            project.pinned
              ? "text-yellow-500 hover:bg-yellow-50"
              : "text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          }`}
          onClick={handlePinClick}
          title={project.pinned ? "Unpin project" : "Pin project"}
          type="button"
        >
          <svg
            className="h-5 w-5"
            fill={project.pinned ? "currentColor" : "none"}
            stroke="currentColor"
            strokeWidth={2}
            viewBox="0 0 24 24"
          >
            <path
              d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </div>

      {/* Health counts grid */}
      <div className="mt-4 grid grid-cols-4 gap-2 text-center">
        <div className="rounded bg-gray-50 p-2">
          <span className="block text-lg font-semibold text-gray-900">
            {project.health.taskCount}
          </span>
          <span className="text-xs text-gray-500">Tasks</span>
        </div>
        <div className="rounded bg-gray-50 p-2">
          <span className="block text-lg font-semibold text-gray-900">
            {project.health.sessionCount}
          </span>
          <span className="text-xs text-gray-500">Sessions</span>
        </div>
        <div className="rounded bg-gray-50 p-2">
          <span className="block text-lg font-semibold text-gray-900">
            {project.health.qaCount}
          </span>
          <span className="text-xs text-gray-500">QA</span>
        </div>
        <div className="rounded bg-blue-50 p-2">
          <span className="block text-lg font-semibold text-blue-600">
            {project.health.activeCount}
          </span>
          <span className="text-xs text-blue-600">Active</span>
        </div>
      </div>

      {/* Footer with last activity and link */}
      <div className="mt-4 flex items-center justify-between border-t pt-3">
        <span className="text-sm text-gray-500">
          Last activity: {formatRelativeTime(project.lastActivityAt)}
        </span>
        <Link
          aria-label="View project"
          className="text-sm font-medium text-blue-600 hover:text-blue-800"
          href={`/projects/${project.projectId}`}
        >
          View project &rarr;
        </Link>
      </div>
    </article>
  );
}
