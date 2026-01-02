"use client";

import { ProjectCard } from "./ProjectCard";
import type { Project } from "./types";

interface ProjectListProps {
  projects: Project[];
  isLoading: boolean;
  error?: string;
  onPin?: (projectId: string, pinned: boolean) => void;
}

export function ProjectList({
  projects,
  isLoading,
  error,
  onPin,
}: ProjectListProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12" role="status">
        <div className="flex items-center gap-2">
          <svg
            className="h-5 w-5 animate-spin text-blue-600"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              fill="currentColor"
            />
          </svg>
          <span className="text-gray-600">Loading projects...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="rounded-lg border border-red-200 bg-red-50 p-4"
        role="alert"
      >
        <div className="flex items-center gap-2">
          <svg
            className="h-5 w-5 text-red-600"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            viewBox="0 0 24 24"
          >
            <path
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <span className="font-medium text-red-800">
            Failed to load projects
          </span>
        </div>
        <p className="mt-2 text-sm text-red-700">{error}</p>
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-gray-300 p-8 text-center">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          stroke="currentColor"
          strokeWidth={1}
          viewBox="0 0 24 24"
        >
          <path
            d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <h3 className="mt-4 text-lg font-medium text-gray-900">
          No projects found
        </h3>
        <p className="mt-2 text-sm text-gray-500">
          Configure scan roots to discover Edison projects.
        </p>
      </div>
    );
  }

  // Separate pinned and unpinned projects
  const pinnedProjects = projects.filter((p) => p.pinned);
  const unpinnedProjects = projects.filter((p) => !p.pinned);

  return (
    <div className="space-y-6">
      {/* Project count */}
      <p className="text-sm text-gray-600">
        {projects.length} project{projects.length !== 1 ? "s" : ""}
      </p>

      {/* Pinned section */}
      {pinnedProjects.length > 0 && (
        <section>
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-gray-500">
            Pinned
          </h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {pinnedProjects.map((project) => (
              <ProjectCard key={project.projectId} onPin={onPin} project={project} />
            ))}
          </div>
        </section>
      )}

      {/* All projects section */}
      <section>
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-gray-500">
          All Projects
        </h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {unpinnedProjects.map((project) => (
            <ProjectCard key={project.projectId} onPin={onPin} project={project} />
          ))}
        </div>
      </section>
    </div>
  );
}
