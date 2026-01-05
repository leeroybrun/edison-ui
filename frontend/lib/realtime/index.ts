/**
 * Realtime module exports for Edison UI.
 *
 * This module provides WebSocket-based realtime data subscriptions
 * with per-subscription stores and revision ordering.
 */

// Types
export type {
  ResourceType,
  Entity,
  SubscribeMessage,
  UnsubscribeMessage,
  SnapshotMessage,
  UpsertMessage,
  DeleteMessage,
  ErrorMessage,
  ServerMessage,
  ClientMessage,
  SubscriptionState,
  ConnectionState,
  WebSocketClientConfig,
} from "./types";

export { parseServerMessage } from "./types";

// Subscription Store
export { SubscriptionStore } from "./subscription-store";

// WebSocket Client
export {
  WebSocketClient,
  getSharedWebSocketClient,
  resetSharedWebSocketClient,
} from "./websocket-client";
export type { MessageHandler, ConnectionHandler } from "./websocket-client";

// React Hook
export { useSubscription } from "./use-subscription";
export type { UseSubscriptionResult } from "./use-subscription";
