"use client";

import { useState, useEffect } from "react";

import type {
  SessionContextResponse,
  SessionContextPanelProps,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type ViewMode = "markdown" | "json";

/**
 * SessionContextPanel displays session context information.
 * Provides toggle between rendered markdown view and raw JSON.
 */
export function SessionContextPanel({
  projectId,
  sessionId,
}: SessionContextPanelProps) {
  const [context, setContext] = useState<SessionContextResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("markdown");

  useEffect(() => {
    async function fetchContext() {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `${API_BASE_URL}/api/v1/projects/${projectId}/sessions/${sessionId}/context`,
          { cache: "no-store" }
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch: ${response.statusText}`);
        }

        const data = await response.json();
        setContext(data);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load session context"
        );
      } finally {
        setIsLoading(false);
      }
    }

    fetchContext();
  }, [projectId, sessionId]);

  if (isLoading) {
    return (
      <div
        role="status"
        aria-label="Loading session context"
        className="flex items-center justify-center p-8"
      >
        <div className="flex items-center gap-2 text-gray-500">
          <svg
            className="h-5 w-5 animate-spin"
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
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          <span>Loading session context...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        role="alert"
        className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700"
      >
        <p className="font-medium">Failed to load session context</p>
        <p className="text-sm">{error}</p>
      </div>
    );
  }

  if (!context) {
    return (
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center text-gray-500">
        <p>No context available for this session.</p>
      </div>
    );
  }

  return (
    <section
      role="region"
      aria-label="Session context"
      className="space-y-4"
    >
      {/* View mode toggle */}
      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={() => setViewMode("markdown")}
          aria-pressed={viewMode === "markdown"}
          className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
            viewMode === "markdown"
              ? "bg-blue-100 text-blue-700"
              : "bg-gray-100 text-gray-600 hover:bg-gray-200"
          }`}
        >
          Markdown
        </button>
        <button
          type="button"
          onClick={() => setViewMode("json")}
          aria-pressed={viewMode === "json"}
          className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
            viewMode === "json"
              ? "bg-blue-100 text-blue-700"
              : "bg-gray-100 text-gray-600 hover:bg-gray-200"
          }`}
        >
          JSON
        </button>
      </div>

      {viewMode === "json" ? (
        <pre
          role="code"
          className="overflow-auto rounded-lg border border-gray-200 bg-gray-900 p-4 text-sm text-gray-100"
        >
          <code>{JSON.stringify(context, null, 2)}</code>
        </pre>
      ) : (
        <div className="space-y-6 rounded-lg border border-gray-200 bg-white p-6">
          {/* Edison Project Status */}
          <div className="flex items-center gap-2">
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                context.isEdisonProject
                  ? "bg-green-100 text-green-800"
                  : "bg-gray-100 text-gray-600"
              }`}
            >
              {context.isEdisonProject ? "Edison Project" : "Not Edison"}
            </span>
          </div>

          {/* Session State */}
          <div>
            <h3 className="text-sm font-medium text-gray-500">Session State</h3>
            <p className="mt-1 text-lg font-semibold text-gray-900">
              {context.sessionState}
            </p>
          </div>

          {/* Current Task */}
          {context.currentTaskId && (
            <div>
              <h3 className="text-sm font-medium text-gray-500">
                Current Task
              </h3>
              <p className="mt-1 font-mono text-lg font-semibold text-blue-600">
                {context.currentTaskId}
              </p>
            </div>
          )}

          {/* Active Packs */}
          {context.activePacks.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-500">Active Packs</h3>
              <ul className="mt-2 flex flex-wrap gap-2">
                {context.activePacks.map((pack) => (
                  <li
                    key={pack}
                    className="inline-flex items-center rounded-md bg-purple-50 px-2 py-1 text-sm font-medium text-purple-700"
                  >
                    {pack}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Current Task State */}
          {context.currentTaskState && (
            <div>
              <h3 className="text-sm font-medium text-gray-500">
                Current Task State
              </h3>
              <p className="mt-1 text-lg font-semibold text-gray-900">
                {context.currentTaskState}
              </p>
            </div>
          )}

          {/* Constitutions */}
          {Object.keys(context.constitutions).length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-500">
                Constitutions
              </h3>
              <dl className="mt-2 space-y-1">
                {Object.entries(context.constitutions).map(([name, path]) => (
                  <div key={name} className="flex gap-2">
                    <dt className="font-medium text-gray-600">{name}:</dt>
                    <dd className="font-mono text-sm text-gray-500">{path}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}

          {/* Paths */}
          <div>
            <h3 className="text-sm font-medium text-gray-500">Paths</h3>
            <dl className="mt-2 space-y-1 text-sm">
              <div className="flex gap-2">
                <dt className="font-medium text-gray-600">Project Root:</dt>
                <dd className="font-mono text-gray-500">
                  {context.projectRoot}
                </dd>
              </div>
              {context.worktreePath && (
                <div className="flex gap-2">
                  <dt className="font-medium text-gray-600">Worktree:</dt>
                  <dd className="font-mono text-gray-500">
                    {context.worktreePath}
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {/* Timestamp */}
          {context.timestamp && (
            <div className="border-t border-gray-100 pt-4 text-xs text-gray-400">
              Context computed at {new Date(context.timestamp).toLocaleString()}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
