"use client";

import { useState, useEffect, useCallback } from "react";

import { PreviewConfirmDialog } from "../Dialogs/PreviewConfirmDialog";
import type {
  GuardFailure,
  GuardWarning,
  TransitionPreview,
  TransitionResult,
} from "../Dialogs/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface TaskTransitionDialogProps {
  /** Task ID to transition */
  taskId: string;
  /** Project ID containing the task */
  projectId: string;
  /** Target state for the transition */
  toState: string;
  /** Whether the dialog is open */
  open: boolean;
  /** Callback when dialog should close */
  onClose: () => void;
  /** Callback when transition succeeds */
  onSuccess: (result: TransitionResult) => void;
}

/**
 * State badge color mappings for display
 */
const STATE_COLORS: Record<string, string> = {
  todo: "bg-gray-100 text-gray-800",
  wip: "bg-blue-100 text-blue-800",
  blocked: "bg-red-100 text-red-800",
  done: "bg-green-100 text-green-800",
  validated: "bg-purple-100 text-purple-800",
};

/**
 * TaskTransitionDialog handles the preview/confirm flow for task state transitions.
 *
 * Features:
 * - Fetches transition preview on open
 * - Displays current and target states
 * - Shows guard failures that block transitions
 * - Shows guard warnings for non-blocking issues
 * - Confirms transition and calls onSuccess
 */
export function TaskTransitionDialog({
  taskId,
  projectId,
  toState,
  open,
  onClose,
  onSuccess,
}: TaskTransitionDialogProps) {
  const [loading, setLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [preview, setPreview] = useState<TransitionPreview | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Fetch preview when dialog opens
  useEffect(() => {
    if (!open) {
      // Reset state when closed
      setPreview(null);
      setError(null);
      return;
    }

    const fetchPreview = async () => {
      setPreviewLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `${API_BASE_URL}/api/v1/projects/${projectId}/tasks/${taskId}/transition/preview`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ toState }),
          },
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch preview: ${response.statusText}`);
        }

        const data: TransitionPreview = await response.json();
        setPreview(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load preview");
      } finally {
        setPreviewLoading(false);
      }
    };

    fetchPreview();
  }, [open, projectId, taskId, toState]);

  // Handle confirmation
  const handleConfirm = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/projects/${projectId}/tasks/${taskId}/transition`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ toState, confirmed: true }),
        },
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.error || `Failed to transition: ${response.statusText}`,
        );
      }

      const result: TransitionResult = await response.json();
      onSuccess(result);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to transition");
    } finally {
      setLoading(false);
    }
  }, [projectId, taskId, toState, onSuccess, onClose]);

  if (!open) {
    return null;
  }

  // Show loading state while fetching preview
  if (previewLoading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        <div className="fixed inset-0 bg-black/50" />
        <div
          className="relative z-10 flex items-center justify-center rounded-lg bg-white p-8"
          data-testid="preview-loading"
          role="dialog"
        >
          <svg
            className="h-8 w-8 animate-spin text-blue-600"
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
          <span className="ml-3 text-gray-600">Loading preview...</span>
        </div>
      </div>
    );
  }

  // Create preview component
  const previewComponent = preview ? (
    <div className="space-y-4">
      <div className="flex items-center justify-center gap-4">
        <div className="text-center">
          <div className="text-xs text-gray-500">From</div>
          <span
            className={`inline-block rounded-full px-3 py-1 text-sm font-medium ${STATE_COLORS[preview.currentState || ""] || "bg-gray-100 text-gray-800"}`}
          >
            {preview.currentState || "unknown"}
          </span>
        </div>
        <svg
          className="h-5 w-5 text-gray-400"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          viewBox="0 0 24 24"
        >
          <path
            d="M13 7l5 5m0 0l-5 5m5-5H6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <div className="text-center">
          <div className="text-xs text-gray-500">To</div>
          <span
            className={`inline-block rounded-full px-3 py-1 text-sm font-medium ${STATE_COLORS[preview.toState] || "bg-gray-100 text-gray-800"}`}
          >
            {preview.toState}
          </span>
        </div>
      </div>
    </div>
  ) : null;

  // Map guard failures and warnings
  const guardFailures: GuardFailure[] = preview?.guardFailures || [];
  const guardWarnings: GuardWarning[] = preview?.guardWarnings || [];

  // Add error to guard failures for display
  if (error) {
    guardFailures.push({ guard: "error", reason: error });
  }

  return (
    <PreviewConfirmDialog
      cancelText="Cancel"
      confirmText="Confirm Transition"
      guardFailures={guardFailures}
      guardWarnings={guardWarnings}
      loading={loading}
      onClose={onClose}
      onConfirm={handleConfirm}
      open={true}
      previewComponent={previewComponent}
      title={`Transition Task ${taskId}`}
    />
  );
}
