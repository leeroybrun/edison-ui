"use client";

import type { FormEvent, KeyboardEvent } from "react";
import { useState, useEffect, useCallback, useId } from "react";

import { GuardFailureAlert } from "../Dialogs/GuardFailureAlert";
import type {
  GuardFailure,
  GuardWarning,
  TaskCreatePreview,
  TaskCreateResult,
} from "../Dialogs/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface TaskCreateDialogProps {
  /** Project ID to create task in */
  projectId: string;
  /** Optional session ID to associate with task */
  sessionId: string | null;
  /** Optional parent task ID for subtasks */
  parentId: string | null;
  /** Whether the dialog is open */
  open: boolean;
  /** Callback when dialog should close */
  onClose: () => void;
  /** Callback when task creation succeeds */
  onSuccess: (result: TaskCreateResult) => void;
}

type DialogStep = "input" | "preview" | "confirming";

/**
 * TaskCreateDialog handles the preview/confirm flow for creating new tasks.
 *
 * Features:
 * - Title input with validation
 * - Preview step showing allocated task ID
 * - Guard failure display for blocked creation
 * - Confirmation with loading state
 */
export function TaskCreateDialog({
  projectId,
  sessionId,
  parentId,
  open,
  onClose,
  onSuccess,
}: TaskCreateDialogProps) {
  const titleInputId = useId();

  const [title, setTitle] = useState("");
  const [step, setStep] = useState<DialogStep>("input");
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<TaskCreatePreview | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Reset state when dialog closes
  useEffect(() => {
    if (!open) {
      setTitle("");
      setStep("input");
      setPreview(null);
      setError(null);
    }
  }, [open]);

  // Fetch preview
  const fetchPreview = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const body: Record<string, string> = { title };
      if (sessionId) body.sessionId = sessionId;
      if (parentId) body.parentId = parentId;

      const response = await fetch(
        `${API_BASE_URL}/api/v1/projects/${projectId}/tasks/preview`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(body),
        },
      );

      if (!response.ok) {
        throw new Error("Failed to fetch preview");
      }

      const data: TaskCreatePreview = await response.json();
      setPreview(data);
      setStep("preview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load preview");
    } finally {
      setLoading(false);
    }
  }, [title, sessionId, parentId, projectId]);

  // Handle preview button click
  const handlePreview = useCallback(
    (e: FormEvent) => {
      e.preventDefault();
      if (title.trim()) {
        fetchPreview();
      }
    },
    [title, fetchPreview],
  );

  // Handle creation
  const handleCreate = useCallback(async () => {
    if (!preview) return;

    setLoading(true);
    setError(null);
    setStep("confirming");

    try {
      const body: Record<string, unknown> = {
        title,
        confirmed: true,
      };
      if (sessionId) body.sessionId = sessionId;
      if (parentId) body.parentId = parentId;

      const response = await fetch(
        `${API_BASE_URL}/api/v1/projects/${projectId}/tasks`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(body),
        },
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || "Failed to create task");
      }

      const result: TaskCreateResult = await response.json();
      onSuccess(result);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create task");
      setStep("preview");
    } finally {
      setLoading(false);
    }
  }, [preview, title, sessionId, parentId, projectId, onSuccess, onClose]);

  // Handle escape key
  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLDivElement>) => {
      if (event.key === "Escape" && !loading) {
        onClose();
      }
    },
    [onClose, loading],
  );

  // Handle backdrop click
  const handleBackdropClick = useCallback(() => {
    if (!loading) {
      onClose();
    }
  }, [onClose, loading]);

  if (!open) {
    return null;
  }

  const hasFailures =
    preview?.guardFailures && preview.guardFailures.length > 0;
  const isCreateDisabled = loading || hasFailures || !preview;
  const guardFailures: GuardFailure[] = preview?.guardFailures || [];
  const guardWarnings: GuardWarning[] = preview?.guardWarnings || [];

  // Add error to guard failures for display
  if (error) {
    guardFailures.push({ guard: "error", reason: error });
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      onKeyDown={handleKeyDown}
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50"
        data-testid="dialog-backdrop"
        onClick={handleBackdropClick}
      />

      {/* Dialog */}
      <div
        aria-labelledby="dialog-title"
        aria-modal="true"
        className="relative z-10 w-full max-w-md rounded-lg bg-white p-6 shadow-xl"
        role="dialog"
      >
        {/* Title */}
        <h2 className="text-lg font-semibold text-gray-900" id="dialog-title">
          Create New Task
        </h2>

        {/* Content */}
        <div className="mt-4 space-y-4">
          {/* Guard failures */}
          {guardFailures.length > 0 && (
            <GuardFailureAlert failures={guardFailures} />
          )}

          {/* Guard warnings */}
          {guardWarnings.length > 0 && (
            <div
              className="rounded-lg border border-yellow-200 bg-yellow-50 p-4"
              data-testid="guard-warnings"
            >
              <ul className="space-y-1 text-sm text-yellow-700">
                {guardWarnings.map((warning, index) => (
                  <li key={index}>{warning.message}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Title input form */}
          <form onSubmit={handlePreview}>
            <div className="space-y-2">
              <label
                className="block text-sm font-medium text-gray-700"
                htmlFor={titleInputId}
              >
                Task Title
              </label>
              <input
                autoFocus
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
                disabled={loading || step === "preview"}
                id={titleInputId}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter task title..."
                type="text"
                value={title}
              />
            </div>
          </form>

          {/* Preview display */}
          {preview?.preview && step !== "input" && (
            <div className="rounded-lg bg-gray-50 p-4">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500">Task ID:</span>
                <span className="font-mono font-medium text-gray-900">
                  {preview.preview.taskId}
                </span>
              </div>
              <div className="mt-1 flex items-center gap-2">
                <span className="text-sm text-gray-500">Title:</span>
                <span className="text-sm text-gray-900">
                  {preview.preview.title}
                </span>
              </div>
              {sessionId && (
                <div className="mt-1 flex items-center gap-2">
                  <span className="text-sm text-gray-500">Session:</span>
                  <span className="font-mono text-sm text-gray-900">
                    {sessionId}
                  </span>
                </div>
              )}
              {parentId && (
                <div className="mt-1 flex items-center gap-2">
                  <span className="text-sm text-gray-500">Parent:</span>
                  <span className="font-mono text-sm text-gray-900">
                    {parentId}
                  </span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="mt-6 flex justify-end gap-3">
          <button
            className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={loading}
            onClick={onClose}
            type="button"
          >
            Cancel
          </button>

          {step === "input" && (
            <button
              className="inline-flex items-center rounded-lg bg-gray-600 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-50"
              disabled={!title.trim() || loading}
              onClick={handlePreview}
              type="button"
            >
              {loading && (
                <svg
                  className="mr-2 h-4 w-4 animate-spin"
                  data-testid="loading-spinner"
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
              )}
              Preview
            </button>
          )}

          {(step === "preview" || step === "confirming") && (
            <button
              className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
              disabled={isCreateDisabled}
              onClick={handleCreate}
              type="button"
            >
              {loading && (
                <svg
                  className="mr-2 h-4 w-4 animate-spin"
                  data-testid="loading-spinner"
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
              )}
              {loading ? "Creating..." : "Create Task"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
