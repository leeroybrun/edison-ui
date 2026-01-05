/**
 * SubscriptionStore - Per-subscription store for realtime data.
 *
 * Maintains entity collection with revision-ordered updates.
 * Implements the pattern from FR-006: clients ignore stale revisions.
 */

import type {
  Entity,
  ResourceType,
  SnapshotMessage,
  UpsertMessage,
  DeleteMessage,
  ServerMessage,
} from "./types";

/**
 * Listener callback type for store changes
 */
type StoreListener = () => void;

/**
 * SubscriptionStore manages a collection of entities for a single subscription.
 *
 * Features:
 * - Maintains entities in a Map for O(1) lookup by ID
 * - Tracks lastRevisionApplied for stale update rejection
 * - Notifies listeners on data changes
 * - Supports snapshot, upsert, and delete operations
 */
export class SubscriptionStore<T extends Entity> {
  private readonly subscriptionId: string;
  private readonly resource: ResourceType;
  private data: Map<string, T>;
  private lastRevisionApplied: number;
  private loading: boolean;
  private error: Error | null;
  private listeners: Set<StoreListener>;

  constructor(subscriptionId: string, resource: ResourceType) {
    this.subscriptionId = subscriptionId;
    this.resource = resource;
    this.data = new Map();
    this.lastRevisionApplied = 0;
    this.loading = true;
    this.error = null;
    this.listeners = new Set();
  }

  /**
   * Get the subscription ID
   */
  getSubscriptionId(): string {
    return this.subscriptionId;
  }

  /**
   * Get the resource type
   */
  getResource(): ResourceType {
    return this.resource;
  }

  /**
   * Get all entities as an array
   */
  getData(): T[] {
    return Array.from(this.data.values());
  }

  /**
   * Get entity by ID
   */
  getById(id: string): T | undefined {
    return this.data.get(id);
  }

  /**
   * Get the last applied revision number
   */
  getLastRevision(): number {
    return this.lastRevisionApplied;
  }

  /**
   * Check if store is in loading state
   */
  isLoading(): boolean {
    return this.loading;
  }

  /**
   * Get current error if any
   */
  getError(): Error | null {
    return this.error;
  }

  /**
   * Set error state
   */
  setError(error: Error): void {
    this.error = error;
    this.loading = false;
    this.notifyListeners();
  }

  /**
   * Apply a snapshot message - replaces entire collection
   *
   * @returns true if applied, false if stale
   */
  applySnapshot(message: SnapshotMessage<T>): boolean {
    if (message.subscriptionId !== this.subscriptionId) {
      return false;
    }

    if (message.revision <= this.lastRevisionApplied) {
      return false;
    }

    this.data = new Map();
    for (const entity of message.data) {
      this.data.set(entity.id, entity);
    }

    this.lastRevisionApplied = message.revision;
    this.loading = false;
    this.error = null;
    this.notifyListeners();
    return true;
  }

  /**
   * Apply an upsert message - add or update single entity
   *
   * @returns true if applied, false if stale
   */
  applyUpsert(message: UpsertMessage<T>): boolean {
    if (message.subscriptionId !== this.subscriptionId) {
      return false;
    }

    if (message.revision <= this.lastRevisionApplied) {
      return false;
    }

    this.data.set(message.data.id, message.data);
    this.lastRevisionApplied = message.revision;
    this.notifyListeners();
    return true;
  }

  /**
   * Apply a delete message - remove entity by ID
   *
   * @returns true if applied, false if stale
   */
  applyDelete(message: DeleteMessage): boolean {
    if (message.subscriptionId !== this.subscriptionId) {
      return false;
    }

    if (message.revision <= this.lastRevisionApplied) {
      return false;
    }

    this.data.delete(message.id);
    this.lastRevisionApplied = message.revision;
    this.notifyListeners();
    return true;
  }

  /**
   * Apply any server message - dispatches to appropriate handler
   *
   * @returns true if applied, false if stale or wrong subscription
   */
  applyMessage(message: ServerMessage<T>): boolean {
    switch (message.type) {
      case "snapshot":
        return this.applySnapshot(message);
      case "upsert":
        return this.applyUpsert(message);
      case "delete":
        return this.applyDelete(message);
      case "error":
        // Error messages are handled separately
        return false;
    }
  }

  /**
   * Reset store to initial state
   */
  reset(): void {
    this.data = new Map();
    this.lastRevisionApplied = 0;
    this.loading = true;
    this.error = null;
    this.notifyListeners();
  }

  /**
   * Subscribe to store changes
   *
   * @returns unsubscribe function
   */
  subscribe(listener: StoreListener): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * Notify all listeners of a change
   */
  private notifyListeners(): void {
    for (const listener of this.listeners) {
      listener();
    }
  }
}
