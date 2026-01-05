/**
 * WebSocket Client for Edison UI realtime updates.
 *
 * Handles connection lifecycle, message parsing, and typed handlers.
 * Reconnection logic is deferred to T053.
 */

import type {
  ClientMessage,
  ServerMessage,
  ConnectionState,
  WebSocketClientConfig,
} from "./types";
import { parseServerMessage } from "./types";

/**
 * Default WebSocket endpoint for realtime updates
 */
const DEFAULT_WS_URL = "ws://localhost:8000/api/v1/ws/realtime";

/**
 * Message handler callback type
 */
export type MessageHandler<T> = (message: ServerMessage<T>) => void;

/**
 * Connection state change handler
 */
export type ConnectionHandler = (state: ConnectionState) => void;

/**
 * WebSocketClient manages a WebSocket connection for realtime updates.
 *
 * Features:
 * - Connection lifecycle management
 * - Message parsing and validation via Zod
 * - Typed message handlers per subscription
 * - Connection state tracking
 */
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private connectionState: ConnectionState = "disconnected";
  private messageHandlers: Map<string, MessageHandler<unknown>> = new Map();
  private connectionHandlers: Set<ConnectionHandler> = new Set();
  private globalMessageHandler: MessageHandler<unknown> | null = null;

  constructor(config: WebSocketClientConfig = {}) {
    this.url = config.url ?? DEFAULT_WS_URL;
  }

  /**
   * Get current connection state
   */
  getConnectionState(): ConnectionState {
    return this.connectionState;
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.connectionState === "connected";
  }

  /**
   * Connect to WebSocket server
   */
  connect(): void {
    if (
      this.ws?.readyState === WebSocket.OPEN ||
      this.ws?.readyState === WebSocket.CONNECTING
    ) {
      return;
    }

    this.setConnectionState("connecting");

    try {
      this.ws = new WebSocket(this.url);
      this.setupEventHandlers();
    } catch (error) {
      this.setConnectionState("disconnected");
      throw error;
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.setConnectionState("disconnected");
  }

  /**
   * Send a client message
   */
  send(message: ClientMessage): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error("WebSocket is not connected");
    }
    this.ws.send(JSON.stringify(message));
  }

  /**
   * Register a message handler for a specific subscription
   */
  onMessage<T>(subscriptionId: string, handler: MessageHandler<T>): () => void {
    this.messageHandlers.set(
      subscriptionId,
      handler as MessageHandler<unknown>,
    );
    return () => {
      this.messageHandlers.delete(subscriptionId);
    };
  }

  /**
   * Register a global message handler for all messages
   */
  onAnyMessage<T>(handler: MessageHandler<T>): () => void {
    this.globalMessageHandler = handler as MessageHandler<unknown>;
    return () => {
      this.globalMessageHandler = null;
    };
  }

  /**
   * Register a connection state change handler
   */
  onConnectionChange(handler: ConnectionHandler): () => void {
    this.connectionHandlers.add(handler);
    return () => {
      this.connectionHandlers.delete(handler);
    };
  }

  /**
   * Set up WebSocket event handlers
   */
  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      this.setConnectionState("connected");
    };

    this.ws.onclose = () => {
      this.setConnectionState("disconnected");
    };

    this.ws.onerror = () => {
      // Error will be followed by close event
    };

    this.ws.onmessage = (event: MessageEvent) => {
      this.handleMessage(event.data);
    };
  }

  /**
   * Handle incoming WebSocket message
   */
  private handleMessage(data: string): void {
    try {
      const parsed = JSON.parse(data);
      const message = parseServerMessage(parsed);

      if (!message) {
        console.warn("Invalid message format:", parsed);
        return;
      }

      // Call global handler if set
      if (this.globalMessageHandler) {
        this.globalMessageHandler(message);
      }

      // Call subscription-specific handler
      if ("subscriptionId" in message && message.subscriptionId) {
        const handler = this.messageHandlers.get(message.subscriptionId);
        if (handler) {
          handler(message);
        }
      }
    } catch (error) {
      console.error("Failed to parse WebSocket message:", error);
    }
  }

  /**
   * Set connection state and notify handlers
   */
  private setConnectionState(state: ConnectionState): void {
    if (this.connectionState !== state) {
      this.connectionState = state;
      for (const handler of this.connectionHandlers) {
        handler(state);
      }
    }
  }
}

/**
 * Singleton WebSocket client instance
 */
let sharedClient: WebSocketClient | null = null;

/**
 * Get the shared WebSocket client instance
 */
export function getSharedWebSocketClient(
  config?: WebSocketClientConfig,
): WebSocketClient {
  if (!sharedClient) {
    sharedClient = new WebSocketClient(config);
  }
  return sharedClient;
}

/**
 * Reset the shared client (for testing)
 */
export function resetSharedWebSocketClient(): void {
  if (sharedClient) {
    sharedClient.disconnect();
    sharedClient = null;
  }
}
