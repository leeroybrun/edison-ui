/**
 * useSubscription - React hook for realtime data subscriptions.
 *
 * Provides a simple interface for subscribing to realtime updates
 * with automatic connection management and revision ordering.
 */

import { useEffect, useState, useRef, useMemo } from "react";
import { SubscriptionStore } from "./subscription-store";
import type {
  Entity,
  ResourceType,
  ServerMessage,
  SubscribeMessage,
  UnsubscribeMessage,
} from "./types";

/**
 * Subscription state returned by useSubscription hook
 */
export interface UseSubscriptionResult<T extends Entity> {
  /** Current data array */
  data: T[];
  /** Whether WebSocket is connected */
  isConnected: boolean;
  /** Whether waiting for initial snapshot */
  isLoading: boolean;
  /** Current error if any */
  error: Error | null;
  /** Last applied revision number */
  revision: number;
}

/**
 * Generate a unique subscription ID
 */
function generateSubscriptionId(): string {
  return `sub-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

/**
 * Default WebSocket URL
 */
const DEFAULT_WS_URL = "ws://localhost:8000/api/v1/ws/realtime";

/**
 * useSubscription hook for realtime data subscriptions.
 *
 * Subscribes to a resource and receives realtime updates.
 * Automatically handles:
 * - WebSocket connection
 * - Subscribe/unsubscribe messages
 * - Revision-ordered updates
 * - Error handling
 *
 * @param resource - Resource type to subscribe to
 * @param params - Optional subscription parameters
 * @param wsUrl - Optional WebSocket URL override
 * @returns Subscription state with data, loading, error, etc.
 */
export function useSubscription<T extends Entity>(
  resource: ResourceType,
  params?: Record<string, unknown>,
  wsUrl: string = DEFAULT_WS_URL,
): UseSubscriptionResult<T> {
  // Stable subscription ID for this hook instance - generate once
  const subscriptionIdRef = useRef<string | null>(null);
  if (subscriptionIdRef.current === null) {
    subscriptionIdRef.current = generateSubscriptionId();
  }

  // WebSocket reference
  const wsRef = useRef<WebSocket | null>(null);

  // Store reference - create once
  const storeRef = useRef<SubscriptionStore<T> | null>(null);
  if (storeRef.current === null) {
    storeRef.current = new SubscriptionStore<T>(
      subscriptionIdRef.current,
      resource,
    );
  }

  // Connection state
  const [isConnected, setIsConnected] = useState(false);

  // Version counter to trigger re-renders on store changes
  const [version, setVersion] = useState(0);

  // Memoize params to detect changes - stable stringify
  const paramsKey = useMemo(() => JSON.stringify(params ?? {}), [params]);

  // Track previous params to detect changes for resubscribe
  const prevParamsKeyRef = useRef<string | null>(null);

  // Effect for WebSocket connection and subscription
  useEffect(() => {
    // Check if this is a params change (resubscribe scenario)
    const isParamsChange =
      prevParamsKeyRef.current !== null &&
      prevParamsKeyRef.current !== paramsKey;
    const oldSubscriptionId = subscriptionIdRef.current!;

    // If params changed, generate new subscription ID and reset store
    if (isParamsChange) {
      const newSubscriptionId = generateSubscriptionId();
      subscriptionIdRef.current = newSubscriptionId;
      storeRef.current = new SubscriptionStore<T>(newSubscriptionId, resource);
    }
    prevParamsKeyRef.current = paramsKey;

    const currentSubscriptionId = subscriptionIdRef.current!;
    const store = storeRef.current!;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    const handleMessage = (event: MessageEvent) => {
      try {
        const message = JSON.parse(event.data) as ServerMessage<T>;

        if (
          "subscriptionId" in message &&
          message.subscriptionId !== currentSubscriptionId
        ) {
          return; // Message for different subscription
        }

        let applied = false;
        switch (message.type) {
          case "snapshot":
            applied = store.applySnapshot(message);
            break;
          case "upsert":
            applied = store.applyUpsert(message);
            break;
          case "delete":
            applied = store.applyDelete(message);
            break;
          case "error":
            store.setError(new Error(`${message.code}: ${message.message}`));
            applied = true;
            break;
        }

        if (applied) {
          setVersion((v) => v + 1);
        }
      } catch (error) {
        console.error("Failed to handle WebSocket message:", error);
      }
    };

    const sendSubscribe = () => {
      const message: SubscribeMessage = {
        type: "subscribe",
        subscriptionId: currentSubscriptionId,
        resource,
        params: params,
      };
      ws.send(JSON.stringify(message));
    };

    ws.onopen = () => {
      setIsConnected(true);
      sendSubscribe();
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    ws.onerror = () => {
      store.setError(new Error("WebSocket connection error"));
      setVersion((v) => v + 1);
    };

    ws.onmessage = handleMessage;

    // Cleanup
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        const unsubMessage: UnsubscribeMessage = {
          type: "unsubscribe",
          subscriptionId: currentSubscriptionId,
        };
        ws.send(JSON.stringify(unsubMessage));
      }
      ws.close();
      wsRef.current = null;
    };
  }, [wsUrl, resource, paramsKey, params]);

  // Get current store state
  const store = storeRef.current!;

  return {
    data: store.getData(),
    isConnected,
    isLoading: store.isLoading(),
    error: store.getError(),
    revision: store.getLastRevision(),
  };
}
