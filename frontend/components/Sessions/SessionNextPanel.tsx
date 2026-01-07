"use client";

import { useState, useEffect } from "react";

import type {
  SessionNextResponse,
  SessionNextPanelProps,
  SuggestedAction,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type ViewMode = "rendered" | "json";

/**
 * Get styling for action type badges.
 */
function getActionTypeStyles(actionType: string): string {
  switch (actionType) {
    case "claim":
      return "bg-blue-100 text-blue-700";
    case "validate":
      return "bg-green-100 text-green-700";
    case "review":
      return "bg-yellow-100 text-yellow-700";
    case "complete":
      return "bg-emerald-100 text-emerald-700";
    case "pause":
      return "bg-orange-100 text-orange-700";
    default:
      return "bg-gray-100 text-gray-700";
  }
}

/**
 * Render a single suggested action item.
 */
function SuggestedActionItem({ action }: { action: SuggestedAction }) {
  const ariaLabel = action.taskId
    ? `${action.actionType} ${action.taskId}`
    : action.actionType;

  return (
    <li
      role="listitem"
      aria-label={ariaLabel}
      className="flex items-start gap-3 rounded-lg border border-gray-100 bg-white p-4 transition-colors hover:bg-gray-50"
    >
      <span
        className={`inline-flex shrink-0 items-center rounded-md px-2 py-1 text-xs font-medium ${getActionTypeStyles(
          action.actionType
        )}`}
      >
        {action.actionType}
      </span>
      <div className="min-w-0 flex-1">
        {action.taskId && (
          <p className="font-mono text-sm font-semibold text-blue-600">
            {action.taskId}
          </p>
        )}
        <p className="text-sm text-gray-600">{action.reason}</p>
      </div>
    </li>
  );
}

/**
 * SessionNextPanel displays session next recommendations.
 * Provides toggle between rendered view and raw JSON.
 */
export function SessionNextPanel({
  projectId,
  sessionId,
}: SessionNextPanelProps) {
  const [next, setNext] = useState<SessionNextResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("rendered");

  useEffect(() => {
    async function fetchNext() {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `${API_BASE_URL}/api/v1/projects/${projectId}/sessions/${sessionId}/next`,
          { cache: "no-store" }
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch: ${response.statusText}`);
        }

        const data = await response.json();
        setNext(data);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load next recommendations"
        );
      } finally {
        setIsLoading(false);
      }
    }

    fetchNext();
  }, [projectId, sessionId]);

  if (isLoading) {
    return (
      <div
        role="status"
        aria-label="Loading next recommendations"
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
          <span>Loading next recommendations...</span>
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
        <p className="font-medium">Failed to load next recommendations</p>
        <p className="text-sm">{error}</p>
      </div>
    );
  }

  if (!next) {
    return (
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center text-gray-500">
        <p>No recommendations available for this session.</p>
      </div>
    );
  }

  return (
    <section role="region" aria-label="Session next" className="space-y-4">
      {/* View mode toggle */}
      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={() => setViewMode("rendered")}
          aria-pressed={viewMode === "rendered"}
          className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
            viewMode === "rendered"
              ? "bg-blue-100 text-blue-700"
              : "bg-gray-100 text-gray-600 hover:bg-gray-200"
          }`}
        >
          Rendered
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
          <code>{JSON.stringify(next, null, 2)}</code>
        </pre>
      ) : (
        <div className="space-y-6">
          {/* Recommendation markdown */}
          <div className="rounded-lg border border-gray-200 bg-white p-6">
            <div className="prose prose-sm max-w-none">
              {/* Simple markdown rendering - headers and paragraphs */}
              {next.recommendation.split("\n").map((line, index) => {
                const trimmedLine = line.trim();
                if (trimmedLine.startsWith("## ")) {
                  return (
                    <h2
                      key={index}
                      className="mt-4 text-lg font-semibold text-gray-900 first:mt-0"
                    >
                      {trimmedLine.slice(3)}
                    </h2>
                  );
                }
                if (trimmedLine.startsWith("# ")) {
                  return (
                    <h1
                      key={index}
                      className="mt-4 text-xl font-bold text-gray-900 first:mt-0"
                    >
                      {trimmedLine.slice(2)}
                    </h1>
                  );
                }
                if (trimmedLine) {
                  return (
                    <p key={index} className="mt-2 text-gray-700">
                      {trimmedLine}
                    </p>
                  );
                }
                return null;
              })}
            </div>
          </div>

          {/* Suggested Actions */}
          {next.suggestedActions.length > 0 && (
            <div>
              <h3 className="mb-3 text-sm font-medium text-gray-500">
                Suggested Actions
              </h3>
              <ul role="list" className="space-y-2">
                {next.suggestedActions.map((action, index) => (
                  <SuggestedActionItem key={index} action={action} />
                ))}
              </ul>
            </div>
          )}

          {/* Timestamp */}
          {next.timestamp && (
            <div className="text-xs text-gray-400">
              Computed at{" "}
              {isNaN(new Date(next.timestamp).getTime())
                ? next.timestamp
                : new Date(next.timestamp).toLocaleString()}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
