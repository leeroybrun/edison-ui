"use client";

import type { GuardFailure } from "./types";

export interface GuardFailureAlertProps {
  /** Array of guard failures to display */
  failures: GuardFailure[];
  /** Optional custom title for the alert */
  title?: string;
}

/**
 * GuardFailureAlert displays guard failures in an alert banner.
 *
 * Features:
 * - Red/error styling to indicate blocked action
 * - Lists each guard failure with its reason
 * - Accessible with role="alert" for screen reader announcement
 * - Shows nothing when there are no failures
 */
export function GuardFailureAlert({
  failures,
  title = "Action Blocked",
}: GuardFailureAlertProps) {
  if (failures.length === 0) {
    return null;
  }

  return (
    <div
      className="rounded-lg border border-red-200 bg-red-50 p-4"
      role="alert"
    >
      <div className="flex items-start">
        <svg
          aria-hidden="true"
          className="h-5 w-5 flex-shrink-0 text-red-400"
          data-testid="guard-failure-icon"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            clipRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
            fillRule="evenodd"
          />
        </svg>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-red-800">{title}</h3>
          <ul className="mt-2 space-y-1 text-sm text-red-700" role="list">
            {failures.map((failure, index) => (
              <li className="flex flex-col" key={index}>
                <span className="font-mono text-xs text-red-600">
                  {failure.guard}
                </span>
                <span>{failure.reason}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
