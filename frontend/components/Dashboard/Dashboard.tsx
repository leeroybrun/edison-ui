"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ProjectList } from "./ProjectList";
import type { Project, ProjectListResponse } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface DashboardSummary {
  totalTasks: number;
  totalActive: number;
  totalSessions: number;
  totalQA: number;
}

function calculateSummary(projects: Project[]): DashboardSummary {
  return projects.reduce(
    (acc, project) => ({
      totalTasks: acc.totalTasks + project.health.taskCount,
      totalActive: acc.totalActive + project.health.activeCount,
      totalSessions: acc.totalSessions + project.health.sessionCount,
      totalQA: acc.totalQA + project.health.qaCount,
    }),
    { totalTasks: 0, totalActive: 0, totalSessions: 0, totalQA: 0 },
  );
}

export function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | undefined>();

  const fetchProjects = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(undefined);

      const response = await fetch(`${API_BASE_URL}/api/v1/projects`);
      if (!response.ok) {
        throw new Error(`Failed to fetch projects: ${response.statusText}`);
      }

      const data: ProjectListResponse = await response.json();
      setProjects(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const handlePin = useCallback(
    async (projectId: string, pinned: boolean) => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/v1/projects/${projectId}/pin`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pinned }),
          },
        );

        if (!response.ok) {
          throw new Error("Failed to update pin status");
        }

        // Refetch projects to get updated state
        await fetchProjects();
      } catch (err) {
        console.error("Failed to pin project:", err);
      }
    },
    [fetchProjects],
  );

  const summary = calculateSummary(projects);
  const hasNoProjects = !isLoading && !error && projects.length === 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <button
          className="text-sm text-gray-500 hover:text-gray-700"
          onClick={() => fetchProjects()}
          type="button"
        >
          Refresh
        </button>
      </div>

      {/* Summary stats (only show when we have data) */}
      {!isLoading && !error && projects.length > 0 && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="rounded-lg border bg-white p-4">
            <span className="block text-2xl font-bold text-gray-900">
              {summary.totalTasks}
            </span>
            <span className="text-sm text-gray-500">Total Tasks</span>
          </div>
          <div className="rounded-lg border bg-white p-4">
            <span className="block text-2xl font-bold text-blue-600">
              {summary.totalActive}
            </span>
            <span className="text-sm text-gray-500">Active</span>
          </div>
          <div className="rounded-lg border bg-white p-4">
            <span className="block text-2xl font-bold text-gray-900">
              {summary.totalSessions}
            </span>
            <span className="text-sm text-gray-500">Sessions</span>
          </div>
          <div className="rounded-lg border bg-white p-4">
            <span className="block text-2xl font-bold text-gray-900">
              {summary.totalQA}
            </span>
            <span className="text-sm text-gray-500">QA Items</span>
          </div>
        </div>
      )}

      {/* Projects list */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-gray-900">Projects</h2>
        <ProjectList
          error={error}
          isLoading={isLoading}
          onPin={handlePin}
          projects={projects}
        />
        {hasNoProjects && (
          <div className="mt-4 text-center">
            <Link
              className="text-sm font-medium text-blue-600 hover:text-blue-800"
              href="/settings"
            >
              Configure scan roots &rarr;
            </Link>
          </div>
        )}
      </section>

      {/* Recent activity section */}
      {!isLoading && projects.length > 0 && (
        <section>
          <h2 className="mb-4 text-lg font-semibold text-gray-900">
            Recent Activity
          </h2>
          <div className="rounded-lg border bg-white p-4">
            <p className="text-sm text-gray-500">
              Activity feed coming soon. View individual projects for detailed
              activity logs.
            </p>
          </div>
        </section>
      )}
    </div>
  );
}
