/**
 * Realtime subscription types for Edison UI.
 *
 * Defines message types for WebSocket-based realtime updates
 * following the per-subscription store pattern with revision ordering.
 */

import { z } from "zod";

/**
 * Supported resource types for subscriptions
 */
export type ResourceType = "tasks" | "sessions" | "qa" | "projects";

/**
 * Base entity with ID for store operations
 */
export interface Entity {
  id: string;
}

/**
 * Client-to-server: Subscribe to a resource
 */
export interface SubscribeMessage {
  type: "subscribe";
  subscriptionId: string;
  resource: ResourceType;
  params?: Record<string, unknown>;
}

/**
 * Client-to-server: Unsubscribe from a resource
 */
export interface UnsubscribeMessage {
  type: "unsubscribe";
  subscriptionId: string;
}

/**
 * Server-to-client: Full snapshot of data
 */
export interface SnapshotMessage<T> {
  type: "snapshot";
  subscriptionId: string;
  revision: number;
  data: T[];
}

/**
 * Server-to-client: Upsert (add or update) a single entity
 */
export interface UpsertMessage<T> {
  type: "upsert";
  subscriptionId: string;
  revision: number;
  data: T;
}

/**
 * Server-to-client: Delete an entity
 */
export interface DeleteMessage {
  type: "delete";
  subscriptionId: string;
  revision: number;
  id: string;
}

/**
 * Server-to-client: Error message
 */
export interface ErrorMessage {
  type: "error";
  subscriptionId?: string;
  code: string;
  message: string;
}

/**
 * Union of all server-to-client message types
 */
export type ServerMessage<T> =
  | SnapshotMessage<T>
  | UpsertMessage<T>
  | DeleteMessage
  | ErrorMessage;

/**
 * Union of all client-to-server message types
 */
export type ClientMessage = SubscribeMessage | UnsubscribeMessage;

/**
 * Subscription state tracked per subscription
 */
export interface SubscriptionState<T extends Entity> {
  subscriptionId: string;
  resource: ResourceType;
  params?: Record<string, unknown>;
  lastRevisionApplied: number;
  data: Map<string, T>;
  isLoading: boolean;
  error: Error | null;
}

/**
 * Connection state for WebSocket client
 */
export type ConnectionState =
  | "disconnected"
  | "connecting"
  | "connected"
  | "reconnecting";

/**
 * WebSocket client configuration
 */
export interface WebSocketClientConfig {
  url?: string;
  reconnectIntervalMs?: number;
  maxReconnectAttempts?: number;
}

/**
 * Zod schemas for runtime validation
 */
export const SnapshotMessageSchema = z.object({
  type: z.literal("snapshot"),
  subscriptionId: z.string(),
  revision: z.number(),
  data: z.array(z.unknown()),
});

export const UpsertMessageSchema = z.object({
  type: z.literal("upsert"),
  subscriptionId: z.string(),
  revision: z.number(),
  data: z.unknown(),
});

export const DeleteMessageSchema = z.object({
  type: z.literal("delete"),
  subscriptionId: z.string(),
  revision: z.number(),
  id: z.string(),
});

export const ErrorMessageSchema = z.object({
  type: z.literal("error"),
  subscriptionId: z.string().optional(),
  code: z.string(),
  message: z.string(),
});

export const ServerMessageSchema = z.discriminatedUnion("type", [
  SnapshotMessageSchema,
  UpsertMessageSchema,
  DeleteMessageSchema,
  ErrorMessageSchema,
]);

/**
 * Parse and validate a server message
 */
export function parseServerMessage(
  data: unknown,
): ServerMessage<unknown> | null {
  const result = ServerMessageSchema.safeParse(data);
  if (result.success) {
    return result.data as ServerMessage<unknown>;
  }
  return null;
}
