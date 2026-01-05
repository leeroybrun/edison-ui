/**
 * Reconnection Manager for WebSocket realtime connections.
 *
 * Provides:
 * - Exponential backoff on disconnect (1s, 2s, 4s, 8s, max 30s)
 * - Maximum reconnection attempts (configurable, default 10)
 * - Re-subscription tracking for reconnect
 * - Connection state management
 */

/**
 * Connection state types
 */
export type ConnectionState =
  | "disconnected"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "polling";

/**
 * Subscription info for re-subscription on reconnect
 */
export interface SubscriptionInfo {
  channel: string;
  params?: Record<string, unknown>;
}

/**
 * Reconnection manager configuration
 */
export interface ReconnectionConfig {
  /** Maximum number of reconnection attempts (default: 10) */
  maxAttempts: number;
  /** Initial delay in ms before first reconnect (default: 1000) */
  initialDelay: number;
  /** Maximum delay in ms between reconnects (default: 30000) */
  maxDelay: number;
}

/**
 * Reconnection manager interface
 */
export interface ReconnectionManager {
  /** Get current configuration */
  getConfig(): ReconnectionConfig;

  /** Calculate delay for a given attempt number */
  getDelayForAttempt(attempt: number): number;

  /** Get current attempt count */
  getAttemptCount(): number;

  /** Record a reconnection attempt */
  recordAttempt(): void;

  /** Reset attempt count (on successful connection) */
  resetAttempts(): void;

  /** Check if max attempts have been exhausted */
  hasExhaustedAttempts(): boolean;

  /** Schedule a reconnection with appropriate delay */
  scheduleReconnect(callback: () => void): boolean;

  /** Cancel pending reconnection */
  cancelReconnect(): void;

  /** Get next reconnect time (timestamp) or null */
  getNextReconnectTime(): number | null;

  /** Add subscription for re-subscription on reconnect */
  addSubscription(channel: string, params?: Record<string, unknown>): void;

  /** Remove subscription */
  removeSubscription(channel: string): void;

  /** Clear all subscriptions */
  clearSubscriptions(): void;

  /** Get all tracked subscriptions */
  getSubscriptions(): SubscriptionInfo[];

  /** Set callback for reconnect (called with subscriptions) */
  setOnReconnect(callback: (subscriptions: SubscriptionInfo[]) => void): void;

  /** Trigger reconnect callback manually */
  triggerReconnectCallback(): void;

  /** Get current connection state */
  getState(): ConnectionState;

  /** Set connection state */
  setState(state: ConnectionState): void;

  /** Register state change listener */
  onStateChange(
    callback: (newState: ConnectionState, oldState: ConnectionState) => void,
  ): () => void;

  /** Reset manager state (preserves subscriptions) */
  reset(): void;
}

/**
 * Create a reconnection manager with optional configuration
 */
export function createReconnectionManager(
  config?: Partial<ReconnectionConfig>,
): ReconnectionManager {
  const fullConfig: ReconnectionConfig = {
    maxAttempts: config?.maxAttempts ?? 10,
    initialDelay: config?.initialDelay ?? 1000,
    maxDelay: config?.maxDelay ?? 30000,
  };

  let attemptCount = 0;
  let state: ConnectionState = "disconnected";
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let nextReconnectTime: number | null = null;

  const subscriptions = new Map<string, SubscriptionInfo>();
  const stateChangeListeners = new Set<
    (newState: ConnectionState, oldState: ConnectionState) => void
  >();
  let onReconnectCallback:
    | ((subscriptions: SubscriptionInfo[]) => void)
    | null = null;

  function getDelayForAttempt(attempt: number): number {
    const delay = fullConfig.initialDelay * Math.pow(2, attempt);
    return Math.min(delay, fullConfig.maxDelay);
  }

  function notifyStateChange(
    newState: ConnectionState,
    oldState: ConnectionState,
  ): void {
    for (const listener of stateChangeListeners) {
      listener(newState, oldState);
    }
  }

  return {
    getConfig(): ReconnectionConfig {
      return { ...fullConfig };
    },

    getDelayForAttempt,

    getAttemptCount(): number {
      return attemptCount;
    },

    recordAttempt(): void {
      attemptCount++;
    },

    resetAttempts(): void {
      attemptCount = 0;
    },

    hasExhaustedAttempts(): boolean {
      return attemptCount >= fullConfig.maxAttempts;
    },

    scheduleReconnect(callback: () => void): boolean {
      if (attemptCount >= fullConfig.maxAttempts) {
        return false;
      }

      const delay = getDelayForAttempt(attemptCount);
      nextReconnectTime = Date.now() + delay;

      reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        nextReconnectTime = null;
        callback();
      }, delay);

      return true;
    },

    cancelReconnect(): void {
      if (reconnectTimer !== null) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
        nextReconnectTime = null;
      }
    },

    getNextReconnectTime(): number | null {
      return nextReconnectTime;
    },

    addSubscription(channel: string, params?: Record<string, unknown>): void {
      subscriptions.set(channel, { channel, params });
    },

    removeSubscription(channel: string): void {
      subscriptions.delete(channel);
    },

    clearSubscriptions(): void {
      subscriptions.clear();
    },

    getSubscriptions(): SubscriptionInfo[] {
      return Array.from(subscriptions.values());
    },

    setOnReconnect(callback: (subs: SubscriptionInfo[]) => void): void {
      onReconnectCallback = callback;
    },

    triggerReconnectCallback(): void {
      if (onReconnectCallback) {
        onReconnectCallback(Array.from(subscriptions.values()));
      }
    },

    getState(): ConnectionState {
      return state;
    },

    setState(newState: ConnectionState): void {
      const oldState = state;
      state = newState;
      if (oldState !== newState) {
        notifyStateChange(newState, oldState);
      }
    },

    onStateChange(
      callback: (newState: ConnectionState, oldState: ConnectionState) => void,
    ): () => void {
      stateChangeListeners.add(callback);
      return () => {
        stateChangeListeners.delete(callback);
      };
    },

    reset(): void {
      attemptCount = 0;
      state = "disconnected";
      if (reconnectTimer !== null) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
        nextReconnectTime = null;
      }
      // Subscriptions are preserved for re-subscription
    },
  };
}
