/**
 * StalenessIndicator Component (T053).
 *
 * Displays connection state and data freshness with visual indicators.
 * Supports refresh functionality and accessibility.
 */
"use client";

import { useEffect, useState } from "react";

import { cn } from "../lib/utils";

/**
 * Simple refresh icon as inline SVG
 */
function RefreshIcon({
  className,
  spinning,
}: {
  className?: string;
  spinning?: boolean;
}) {
  return (
    <svg
      className={cn("h-3 w-3", spinning && "animate-spin", className)}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8" />
      <path d="M21 3v5h-5" />
    </svg>
  );
}

type ConnectionState =
  | "connected"
  | "connecting"
  | "disconnected"
  | "polling"
  | "reconnecting";
type StalenessLevel = "fresh" | "stale" | "very_stale" | "unknown";

interface StalenessIndicatorProps {
  lastUpdatedAt: Date | null;
  onRefresh: () => void;
  isRefreshing?: boolean;
  connectionState?: ConnectionState;
  compact?: boolean;
}

const FRESH_THRESHOLD = 5000; // 5 seconds
const STALE_THRESHOLD = 30000; // 30 seconds

function computeStaleness(timestamp: Date | null): StalenessLevel {
  if (timestamp === null) {
    return "unknown";
  }
  const age = Date.now() - timestamp.getTime();
  if (age < FRESH_THRESHOLD) {
    return "fresh";
  } else if (age < STALE_THRESHOLD) {
    return "stale";
  } else {
    return "very_stale";
  }
}

function formatAge(timestamp: Date | null): string {
  if (timestamp === null) {
    return "Never updated";
  }

  const ageMs = Date.now() - timestamp.getTime();

  if (ageMs < 3000) {
    return "Just now";
  }

  const seconds = Math.floor(ageMs / 1000);
  if (seconds < 60) {
    return `${seconds}s ago`;
  }

  const minutes = Math.floor(seconds / 60);
  return `${minutes}m ago`;
}

function getIndicatorColor(staleness: StalenessLevel): string {
  switch (staleness) {
    case "fresh":
      return "bg-green-500";
    case "stale":
      return "bg-yellow-500";
    case "very_stale":
      return "bg-red-500";
    case "unknown":
      return "bg-gray-400";
  }
}

function getStalenessLabel(staleness: StalenessLevel): string {
  switch (staleness) {
    case "fresh":
      return "Data is fresh";
    case "stale":
      return "Data is stale";
    case "very_stale":
      return "Data is very stale";
    case "unknown":
      return "No data received";
  }
}

function getConnectionLabel(state: ConnectionState): string {
  switch (state) {
    case "connected":
      return "Connected";
    case "connecting":
      return "Connecting...";
    case "disconnected":
      return "Disconnected";
    case "polling":
      return "Polling";
    case "reconnecting":
      return "Reconnecting...";
  }
}

export function StalenessIndicator({
  lastUpdatedAt,
  onRefresh,
  isRefreshing = false,
  connectionState,
  compact = false,
}: StalenessIndicatorProps) {
  const [, forceUpdate] = useState({});

  // Update display every second for time-based staleness
  useEffect(() => {
    const interval = setInterval(() => {
      forceUpdate({});
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const staleness = computeStaleness(lastUpdatedAt);
  const ageText = formatAge(lastUpdatedAt);
  const indicatorColor = getIndicatorColor(staleness);
  const stalenessLabel = getStalenessLabel(staleness);

  return (
    <div
      data-testid="staleness-container"
      className={cn("flex items-center gap-2", compact && "compact")}
      role="status"
      aria-live="polite"
    >
      {/* Staleness indicator dot */}
      <span
        data-testid="staleness-indicator"
        className={cn("h-2 w-2 rounded-full", indicatorColor)}
        aria-label={stalenessLabel}
      />

      {/* Time text */}
      <span className="text-sm text-muted-foreground">
        {isRefreshing ? (
          <span aria-label="Refreshing data">Refreshing...</span>
        ) : (
          ageText
        )}
      </span>

      {/* Connection state text (hide in compact mode) */}
      {connectionState && !compact && (
        <span className="text-sm text-muted-foreground">
          {getConnectionLabel(connectionState)}
        </span>
      )}

      {/* Refresh button */}
      <button
        type="button"
        onClick={onRefresh}
        disabled={isRefreshing}
        aria-label="Refresh data"
        className={cn(
          "flex h-6 w-6 items-center justify-center rounded p-0",
          "hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring",
          "disabled:cursor-not-allowed disabled:opacity-50",
        )}
      >
        {isRefreshing ? (
          <span data-testid="refresh-spinner">
            <RefreshIcon spinning />
          </span>
        ) : (
          <RefreshIcon />
        )}
      </button>
    </div>
  );
}
