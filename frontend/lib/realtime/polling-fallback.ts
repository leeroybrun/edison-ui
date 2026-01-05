/**
 * Polling Fallback for realtime data.
 *
 * Provides:
 * - Fallback polling when WebSocket unavailable
 * - Configurable polling interval (default 5000ms)
 * - Multiple subscription support
 * - Pause/resume capability
 * - Manual refresh
 */

/**
 * Polling fallback configuration
 */
export interface PollingConfig {
  /** Polling interval in ms (default: 5000) */
  interval: number;
}

/**
 * Fetch function type for polling
 */
export type PollingFetchFn<T = unknown> = () => Promise<T>;

/**
 * Data handler type
 */
export type PollingDataHandler = (channel: string, data: unknown) => void;

/**
 * Simple data handler (for single fetch mode)
 */
export type SimpleDataHandler = (data: unknown) => void;

/**
 * Error handler type
 */
export type PollingErrorHandler = (error: Error) => void;

/**
 * Polling fallback interface
 */
export interface PollingFallback {
  /** Get current configuration */
  getConfig(): PollingConfig;

  /** Check if polling is active */
  isActive(): boolean;

  /** Check if polling is paused */
  isPaused(): boolean;

  /** Activate polling with a single fetch function */
  activate(fetchFn?: PollingFetchFn): void;

  /** Deactivate polling */
  deactivate(): void;

  /** Pause polling (keeps active state) */
  pause(): void;

  /** Resume polling */
  resume(): void;

  /** Manual refresh (fetches immediately) */
  refresh(): Promise<void>;

  /** Add subscription with fetch function */
  addSubscription(channel: string, fetchFn: PollingFetchFn): void;

  /** Remove subscription */
  removeSubscription(channel: string): void;

  /** Register data handler */
  onData(handler: PollingDataHandler | SimpleDataHandler): void;

  /** Register error handler */
  onError(handler: PollingErrorHandler): void;

  /** Get last poll timestamp */
  getLastPollTime(): number | null;
}

/**
 * Create a polling fallback instance
 */
export function createPollingFallback(
  config?: Partial<PollingConfig>,
): PollingFallback {
  const fullConfig: PollingConfig = {
    interval: config?.interval ?? 5000,
  };

  let active = false;
  let paused = false;
  let pollTimer: ReturnType<typeof setTimeout> | null = null;
  let lastPollTime: number | null = null;
  let singleFetchFn: PollingFetchFn | null = null;

  const subscriptions = new Map<string, PollingFetchFn>();
  const dataHandlers = new Set<PollingDataHandler | SimpleDataHandler>();
  const errorHandlers = new Set<PollingErrorHandler>();

  async function doFetch(): Promise<void> {
    const now = Date.now();
    lastPollTime = now;

    // If single fetch mode
    if (singleFetchFn && subscriptions.size === 0) {
      try {
        const data = await singleFetchFn();
        for (const handler of dataHandlers) {
          // Call as simple handler (single argument)
          (handler as SimpleDataHandler)(data);
        }
      } catch (error) {
        for (const handler of errorHandlers) {
          handler(error instanceof Error ? error : new Error(String(error)));
        }
      }
      return;
    }

    // Multi-subscription mode
    for (const [channel, fetchFn] of subscriptions) {
      try {
        const data = await fetchFn();
        for (const handler of dataHandlers) {
          // Call as channel handler (two arguments)
          (handler as PollingDataHandler)(channel, data);
        }
      } catch (error) {
        for (const handler of errorHandlers) {
          handler(error instanceof Error ? error : new Error(String(error)));
        }
      }
    }
  }

  function schedulePoll(): void {
    if (!active || paused) {
      return;
    }

    pollTimer = setTimeout(async () => {
      pollTimer = null;
      await doFetch();
      schedulePoll();
    }, fullConfig.interval);
  }

  function cancelPoll(): void {
    if (pollTimer !== null) {
      clearTimeout(pollTimer);
      pollTimer = null;
    }
  }

  return {
    getConfig(): PollingConfig {
      return { ...fullConfig };
    },

    isActive(): boolean {
      return active;
    },

    isPaused(): boolean {
      return paused;
    },

    activate(fetchFn?: PollingFetchFn): void {
      active = true;
      paused = false;
      singleFetchFn = fetchFn ?? null;

      // Do initial fetch
      doFetch().then(() => {
        schedulePoll();
      });
    },

    deactivate(): void {
      active = false;
      paused = false;
      singleFetchFn = null;
      cancelPoll();
    },

    pause(): void {
      paused = true;
      cancelPoll();
    },

    resume(): void {
      paused = false;
      if (active) {
        schedulePoll();
      }
    },

    async refresh(): Promise<void> {
      cancelPoll();
      await doFetch();
      if (active && !paused) {
        schedulePoll();
      }
    },

    addSubscription(channel: string, fetchFn: PollingFetchFn): void {
      subscriptions.set(channel, fetchFn);
    },

    removeSubscription(channel: string): void {
      subscriptions.delete(channel);
    },

    onData(handler: PollingDataHandler | SimpleDataHandler): void {
      dataHandlers.add(handler);
    },

    onError(handler: PollingErrorHandler): void {
      errorHandlers.add(handler);
    },

    getLastPollTime(): number | null {
      return lastPollTime;
    },
  };
}
