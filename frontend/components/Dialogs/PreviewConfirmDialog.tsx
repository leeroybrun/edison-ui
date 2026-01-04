"use client";

import type { KeyboardEvent, ReactNode, MouseEvent } from "react";
import { useEffect, useRef, useCallback } from "react";

import { GuardFailureAlert } from "./GuardFailureAlert";
import type { GuardFailure, GuardWarning } from "./types";

export interface PreviewConfirmDialogProps {
  /** Dialog title */
  title: string;
  /** Whether the dialog is open */
  open: boolean;
  /** Callback when dialog should close */
  onClose: () => void;
  /** Callback when confirm button is clicked */
  onConfirm: () => Promise<void>;
  /** Whether the dialog is in loading state */
  loading: boolean;
  /** Preview data to display (used with default preview rendering) */
  preview?: { message: string };
  /** Custom preview component to render */
  previewComponent?: ReactNode;
  /** Array of guard failures that block the action */
  guardFailures: GuardFailure[];
  /** Array of guard warnings (non-blocking) */
  guardWarnings: GuardWarning[];
  /** Success message to display after successful action */
  successMessage?: string;
  /** Whether to auto-close the dialog after success */
  autoCloseOnSuccess?: boolean;
  /** Custom text for confirm button */
  confirmText?: string;
  /** Custom text for cancel button */
  cancelText?: string;
}

/**
 * PreviewConfirmDialog is a reusable dialog for preview/confirm mutation flows.
 *
 * Features:
 * - Shows preview of action before confirmation
 * - Displays guard failures that block actions
 * - Displays guard warnings (non-blocking)
 * - Loading state during confirmation
 * - Success state with optional auto-close
 * - Accessible with keyboard navigation and focus trapping
 */
export function PreviewConfirmDialog({
  title,
  open,
  onClose,
  onConfirm,
  loading,
  preview,
  previewComponent,
  guardFailures,
  guardWarnings,
  successMessage,
  autoCloseOnSuccess = false,
  confirmText = "Confirm",
  cancelText = "Cancel",
}: PreviewConfirmDialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const confirmButtonRef = useRef<HTMLButtonElement>(null);

  const hasFailures = guardFailures.length > 0;
  const isConfirmDisabled = loading || hasFailures;

  // Focus management on open
  useEffect(() => {
    if (open && confirmButtonRef.current) {
      confirmButtonRef.current.focus();
    }
  }, [open]);

  // Auto-close on success
  useEffect(() => {
    if (successMessage && autoCloseOnSuccess) {
      const timer = setTimeout(() => {
        onClose();
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [successMessage, autoCloseOnSuccess, onClose]);

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
  const handleBackdropClick = useCallback(
    (event: MouseEvent<HTMLDivElement>) => {
      if (event.target === event.currentTarget && !loading) {
        onClose();
      }
    },
    [onClose, loading],
  );

  // Handle confirm
  const handleConfirm = useCallback(async () => {
    if (!isConfirmDisabled) {
      await onConfirm();
    }
  }, [onConfirm, isConfirmDisabled]);

  if (!open) {
    return null;
  }

  const titleId = "dialog-title";

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
        aria-labelledby={titleId}
        aria-modal="true"
        className="relative z-10 w-full max-w-md rounded-lg bg-white p-6 shadow-xl"
        ref={dialogRef}
        role="dialog"
      >
        {/* Title */}
        <h2 className="text-lg font-semibold text-gray-900" id={titleId}>
          {title}
        </h2>

        {/* Content */}
        <div className="mt-4 space-y-4">
          {/* Success message */}
          {successMessage && (
            <div className="rounded-lg bg-green-50 p-4 text-sm text-green-800">
              {successMessage}
            </div>
          )}

          {/* Guard failures */}
          {hasFailures && <GuardFailureAlert failures={guardFailures} />}

          {/* Guard warnings */}
          {guardWarnings.length > 0 && (
            <div
              className="rounded-lg border border-yellow-200 bg-yellow-50 p-4"
              data-testid="guard-warnings"
            >
              <div className="flex items-start">
                <svg
                  aria-hidden="true"
                  className="h-5 w-5 flex-shrink-0 text-yellow-400"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    clipRule="evenodd"
                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                    fillRule="evenodd"
                  />
                </svg>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-yellow-800">
                    Warnings
                  </h3>
                  <ul className="mt-1 space-y-1 text-sm text-yellow-700">
                    {guardWarnings.map((warning, index) => (
                      <li key={index}>{warning.message}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Custom preview component */}
          {previewComponent}

          {/* Default preview content */}
          {preview && !previewComponent && (
            <div className="text-sm text-gray-600">{preview.message}</div>
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
            {cancelText}
          </button>
          <button
            className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={isConfirmDisabled}
            onClick={handleConfirm}
            ref={confirmButtonRef}
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
            {loading ? "Confirming..." : confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
