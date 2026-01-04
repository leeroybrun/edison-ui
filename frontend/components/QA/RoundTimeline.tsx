"use client";

import type { KeyboardEvent } from "react";
import { useState } from "react";

import type {
  RoundEvidence,
  RoundTimelineProps,
  ValidatorReport,
} from "./types";

/**
 * Determines if a round has any failing validators
 */
function hasFailingValidator(round: RoundEvidence): boolean {
  return round.validatorReports.some((report) => report.verdict === "fail");
}

/**
 * ValidatorBadge displays a single validator result
 */
function ValidatorBadge({
  report,
  roundNumber,
}: {
  report: ValidatorReport;
  roundNumber: number;
}) {
  const isPassing = report.verdict === "pass";
  const colorClass = isPassing
    ? "bg-green-100 text-green-800"
    : "bg-red-100 text-red-800";

  return (
    <div className="rounded-md border border-gray-200 p-3">
      <div className="mb-2 flex items-center justify-between">
        <span className="font-medium text-gray-900">{report.validatorId}</span>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${colorClass}`}
          data-testid={`validator-badge-${report.validatorId}-round-${roundNumber}`}
        >
          {report.verdict}
        </span>
      </div>
      <p className="text-sm text-gray-600">{report.reason}</p>
      <p className="mt-1 text-xs text-gray-400">
        <span className="font-mono">{report.reportPath}</span>
      </p>
    </div>
  );
}

/**
 * RoundDetails displays the expanded content for a round
 */
function RoundDetails({ round }: { round: RoundEvidence }) {
  return (
    <div className="mt-3 space-y-4 border-t border-gray-100 pt-3">
      {/* Bundle Summary */}
      <div>
        <h4 className="mb-1 text-sm font-medium text-gray-700">Summary</h4>
        <p className="text-sm text-gray-600">{round.bundleSummary}</p>
      </div>

      {/* Implementation Report */}
      {round.implementationReport && (
        <div data-testid={`implementation-report-${round.roundNumber}`}>
          <h4 className="mb-1 text-sm font-medium text-gray-700">
            Implementation Report
          </h4>
          <div className="rounded bg-gray-50 p-2 text-sm text-gray-600">
            {round.implementationReport}
          </div>
        </div>
      )}

      {/* Validator Reports */}
      {round.validatorReports.length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-medium text-gray-700">
            Validator Reports
          </h4>
          <div className="space-y-2">
            {round.validatorReports.map((report) => (
              <ValidatorBadge
                key={report.validatorId}
                report={report}
                roundNumber={round.roundNumber}
              />
            ))}
          </div>
        </div>
      )}

      {/* Artifacts */}
      {round.artifacts.length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-medium text-gray-700">Artifacts</h4>
          <ul className="space-y-1">
            {round.artifacts.map((artifact) => (
              <li key={artifact.name} className="text-sm">
                <a
                  href={artifact.path}
                  className="text-blue-600 hover:underline"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {artifact.name}
                </a>
                <span className="ml-2 text-xs text-gray-400">
                  {artifact.path}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

/**
 * RoundTimeline displays validation rounds as a vertical timeline.
 *
 * Features:
 * - Visual timeline with round indicators
 * - Pass/fail status for each round
 * - Expandable round details
 * - Keyboard accessible
 */
export function RoundTimeline({
  evidence,
  currentRound,
  verdict: _verdict,
}: RoundTimelineProps) {
  // Track which rounds are expanded (current round expanded by default)
  const [expandedRounds, setExpandedRounds] = useState<Set<number>>(() => {
    const initial = new Set<number>();
    if (currentRound > 0) {
      initial.add(currentRound);
    }
    return initial;
  });

  const toggleRound = (roundNumber: number) => {
    setExpandedRounds((prev) => {
      const next = new Set(prev);
      if (next.has(roundNumber)) {
        next.delete(roundNumber);
      } else {
        next.add(roundNumber);
      }
      return next;
    });
  };

  const handleKeyDown = (
    event: KeyboardEvent<HTMLButtonElement>,
    roundNumber: number
  ) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      toggleRound(roundNumber);
    }
  };

  // Empty state
  if (evidence.length === 0) {
    return (
      <div className="py-4 text-center text-sm text-gray-500">
        No validation rounds yet
      </div>
    );
  }

  return (
    <ul className="space-y-0" role="list">
      {evidence.map((round, index) => {
        const isExpanded = expandedRounds.has(round.roundNumber);
        const isCurrent = round.roundNumber === currentRound;
        const hasFailed = hasFailingValidator(round);
        const isLast = index === evidence.length - 1;

        return (
          <li key={round.roundNumber} className="relative">
            {/* Timeline connector */}
            {!isLast && (
              <div
                className="absolute left-4 top-8 h-full w-0.5 bg-gray-200"
                data-testid="timeline-connector"
              />
            )}

            <div className="relative flex gap-3">
              {/* Round indicator */}
              <div
                className={`z-10 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full text-xs font-medium text-white ${
                  hasFailed ? "bg-red-500" : "bg-green-500"
                } ${isCurrent ? "ring-2 ring-blue-500 ring-offset-2" : ""}`}
                data-testid={`round-indicator-${round.roundNumber}`}
              >
                {round.roundNumber}
              </div>

              {/* Round content */}
              <div className="flex-1 pb-4">
                <button
                  className="flex w-full items-center justify-between rounded-lg bg-white p-3 text-left transition-colors hover:bg-gray-50"
                  onClick={() => toggleRound(round.roundNumber)}
                  onKeyDown={(e) => handleKeyDown(e, round.roundNumber)}
                  aria-expanded={isExpanded}
                  aria-label={`Round ${round.roundNumber}`}
                  type="button"
                >
                  <span className="font-medium text-gray-900">
                    Round {round.roundNumber}
                  </span>
                  <svg
                    className={`h-5 w-5 text-gray-400 transition-transform ${
                      isExpanded ? "rotate-180" : ""
                    }`}
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={2}
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path
                      d="M19 9l-7 7-7-7"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </button>

                {isExpanded && <RoundDetails round={round} />}
              </div>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
