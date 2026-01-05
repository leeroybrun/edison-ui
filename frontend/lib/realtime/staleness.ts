/**
 * Staleness Tracking for realtime data.
 *
 * Provides:
 * - Tracks `lastUpdatedAt` timestamp for each subscription
 * - Computes staleness state: `fresh` (< 5s), `stale` (5-30s), `very_stale` (> 30s)
 * - Staleness change events
 * - Formatted age display
 */

/**
 * Staleness levels
 */
export type StalenessLevel = "fresh" | "stale" | "very_stale" | "unknown";

/**
 * Staleness tracker configuration
 */
export interface StalenessConfig {
  /** Threshold for fresh data in ms (default: 5000) */
  freshThreshold: number;
  /** Threshold for stale data in ms (default: 30000) */
  staleThreshold: number;
}

/**
 * Staleness info for a subscription
 */
export interface StalenessInfo {
  lastUpdatedAt: number | null;
  age: number | null;
  staleness: StalenessLevel;
}

/**
 * Staleness change handler
 */
export type StalenessChangeHandler = (
  channel: string,
  newStaleness: StalenessLevel,
  oldStaleness: StalenessLevel | undefined,
) => void;

/**
 * Staleness tracker interface
 */
export interface StalenessTracker {
  /** Get current configuration */
  getConfig(): StalenessConfig;

  /** Record an update for a subscription */
  recordUpdate(channel: string): void;

  /** Get last updated timestamp for a subscription */
  getLastUpdatedAt(channel: string): number | null;

  /** Get staleness level for a subscription */
  getStaleness(channel: string): StalenessLevel;

  /** Get age in milliseconds for a subscription */
  getAge(channel: string): number | null;

  /** Get complete staleness info for a subscription */
  getInfo(channel: string): StalenessInfo;

  /** Get formatted age string */
  getFormattedAge(channel: string): string;

  /** Clear tracking for a subscription */
  clear(channel: string): void;

  /** Clear all tracking */
  clearAll(): void;

  /** Register staleness change handler */
  onStalenessChange(handler: StalenessChangeHandler): () => void;

  /** Manually check staleness (triggers change events if needed) */
  checkStaleness(channel: string): void;

  /** Start automatic staleness checking */
  startAutoCheck(intervalMs: number): void;

  /** Stop automatic staleness checking */
  stopAutoCheck(): void;
}

/**
 * Compute staleness level from a timestamp
 */
export function computeStaleness(
  timestamp: number,
  config?: Partial<StalenessConfig>,
): StalenessLevel {
  const freshThreshold = config?.freshThreshold ?? 5000;
  const staleThreshold = config?.staleThreshold ?? 30000;
  const age = Date.now() - timestamp;

  if (age < freshThreshold) {
    return "fresh";
  } else if (age < staleThreshold) {
    return "stale";
  } else {
    return "very_stale";
  }
}

/**
 * Format age in human readable form
 */
export function formatAge(ageMs: number): string {
  if (ageMs < 1000) {
    return "just now";
  }

  const seconds = Math.floor(ageMs / 1000);
  if (seconds < 60) {
    return `${seconds}s ago`;
  }

  const minutes = Math.floor(seconds / 60);
  return `${minutes}m ago`;
}

/**
 * Create a staleness tracker instance
 */
export function createStalenessTracker(
  config?: Partial<StalenessConfig>,
): StalenessTracker {
  const fullConfig: StalenessConfig = {
    freshThreshold: config?.freshThreshold ?? 5000,
    staleThreshold: config?.staleThreshold ?? 30000,
  };

  const timestamps = new Map<string, number>();
  const stalenessLevels = new Map<string, StalenessLevel>();
  const changeHandlers = new Set<StalenessChangeHandler>();
  let autoCheckTimer: ReturnType<typeof setInterval> | null = null;

  function computeLevel(timestamp: number): StalenessLevel {
    return computeStaleness(timestamp, fullConfig);
  }

  function notifyChange(
    channel: string,
    newLevel: StalenessLevel,
    oldLevel: StalenessLevel | undefined,
  ): void {
    for (const handler of changeHandlers) {
      handler(channel, newLevel, oldLevel);
    }
  }

  function checkAndNotify(channel: string): void {
    const timestamp = timestamps.get(channel);
    if (timestamp === undefined) {
      return;
    }

    const oldLevel = stalenessLevels.get(channel);
    const newLevel = computeLevel(timestamp);

    if (newLevel !== oldLevel) {
      stalenessLevels.set(channel, newLevel);
      notifyChange(channel, newLevel, oldLevel);
    }
  }

  return {
    getConfig(): StalenessConfig {
      return { ...fullConfig };
    },

    recordUpdate(channel: string): void {
      const now = Date.now();
      timestamps.set(channel, now);

      const oldLevel = stalenessLevels.get(channel);
      const newLevel = computeLevel(now);
      stalenessLevels.set(channel, newLevel);

      notifyChange(channel, newLevel, oldLevel);
    },

    getLastUpdatedAt(channel: string): number | null {
      return timestamps.get(channel) ?? null;
    },

    getStaleness(channel: string): StalenessLevel {
      const timestamp = timestamps.get(channel);
      if (timestamp === undefined) {
        return "unknown";
      }
      return computeLevel(timestamp);
    },

    getAge(channel: string): number | null {
      const timestamp = timestamps.get(channel);
      if (timestamp === undefined) {
        return null;
      }
      return Date.now() - timestamp;
    },

    getInfo(channel: string): StalenessInfo {
      const timestamp = timestamps.get(channel);
      if (timestamp === undefined) {
        return {
          lastUpdatedAt: null,
          age: null,
          staleness: "unknown",
        };
      }

      return {
        lastUpdatedAt: timestamp,
        age: Date.now() - timestamp,
        staleness: computeLevel(timestamp),
      };
    },

    getFormattedAge(channel: string): string {
      const age = this.getAge(channel);
      if (age === null) {
        return "";
      }
      return formatAge(age);
    },

    clear(channel: string): void {
      timestamps.delete(channel);
      stalenessLevels.delete(channel);
    },

    clearAll(): void {
      timestamps.clear();
      stalenessLevels.clear();
    },

    onStalenessChange(handler: StalenessChangeHandler): () => void {
      changeHandlers.add(handler);
      return () => {
        changeHandlers.delete(handler);
      };
    },

    checkStaleness(channel: string): void {
      checkAndNotify(channel);
    },

    startAutoCheck(intervalMs: number): void {
      if (autoCheckTimer !== null) {
        clearInterval(autoCheckTimer);
      }

      autoCheckTimer = setInterval(() => {
        for (const channel of timestamps.keys()) {
          checkAndNotify(channel);
        }
      }, intervalMs);
    },

    stopAutoCheck(): void {
      if (autoCheckTimer !== null) {
        clearInterval(autoCheckTimer);
        autoCheckTimer = null;
      }
    },
  };
}
