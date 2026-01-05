/**
 * Tests for SubscriptionStore
 *
 * TDD RED phase: These tests define expected behavior before implementation.
 */

import { describe, it, expect, beforeEach } from "vitest";
import { SubscriptionStore } from "../subscription-store";
import type {
  Entity,
  SnapshotMessage,
  UpsertMessage,
  DeleteMessage,
} from "../types";

interface TestEntity extends Entity {
  id: string;
  name: string;
  value: number;
}

describe("SubscriptionStore", () => {
  let store: SubscriptionStore<TestEntity>;
  const subscriptionId = "test-subscription-1";
  const resource = "tasks" as const;

  beforeEach(() => {
    store = new SubscriptionStore<TestEntity>(subscriptionId, resource);
  });

  describe("initialization", () => {
    it("should initialize with empty data and revision 0", () => {
      expect(store.getData()).toEqual([]);
      expect(store.getLastRevision()).toBe(0);
      expect(store.getSubscriptionId()).toBe(subscriptionId);
      expect(store.getResource()).toBe(resource);
    });

    it("should initialize with isLoading true", () => {
      expect(store.isLoading()).toBe(true);
    });

    it("should have no error initially", () => {
      expect(store.getError()).toBeNull();
    });
  });

  describe("snapshot operations", () => {
    it("should replace entire collection on snapshot", () => {
      const entities: TestEntity[] = [
        { id: "1", name: "Entity 1", value: 10 },
        { id: "2", name: "Entity 2", value: 20 },
      ];

      const message: SnapshotMessage<TestEntity> = {
        type: "snapshot",
        subscriptionId,
        revision: 1,
        data: entities,
      };

      store.applySnapshot(message);

      expect(store.getData()).toEqual(entities);
      expect(store.getLastRevision()).toBe(1);
      expect(store.isLoading()).toBe(false);
    });

    it("should clear previous data on new snapshot", () => {
      // Apply first snapshot
      store.applySnapshot({
        type: "snapshot",
        subscriptionId,
        revision: 1,
        data: [{ id: "1", name: "Old", value: 1 }],
      });

      // Apply second snapshot
      const newEntities: TestEntity[] = [{ id: "2", name: "New", value: 2 }];
      store.applySnapshot({
        type: "snapshot",
        subscriptionId,
        revision: 2,
        data: newEntities,
      });

      expect(store.getData()).toEqual(newEntities);
      expect(store.getById("1")).toBeUndefined();
      expect(store.getById("2")).toEqual(newEntities[0]);
    });

    it("should reject stale snapshot (revision <= lastApplied)", () => {
      store.applySnapshot({
        type: "snapshot",
        subscriptionId,
        revision: 5,
        data: [{ id: "1", name: "Current", value: 5 }],
      });

      // Try to apply older snapshot
      const applied = store.applySnapshot({
        type: "snapshot",
        subscriptionId,
        revision: 3,
        data: [{ id: "2", name: "Stale", value: 3 }],
      });

      expect(applied).toBe(false);
      expect(store.getLastRevision()).toBe(5);
      expect(store.getById("1")).toBeDefined();
      expect(store.getById("2")).toBeUndefined();
    });

    it("should reject snapshot with same revision as lastApplied", () => {
      store.applySnapshot({
        type: "snapshot",
        subscriptionId,
        revision: 5,
        data: [{ id: "1", name: "Current", value: 5 }],
      });

      const applied = store.applySnapshot({
        type: "snapshot",
        subscriptionId,
        revision: 5,
        data: [{ id: "2", name: "Duplicate", value: 5 }],
      });

      expect(applied).toBe(false);
      expect(store.getById("1")).toBeDefined();
      expect(store.getById("2")).toBeUndefined();
    });
  });

  describe("upsert operations", () => {
    beforeEach(() => {
      // Start with a snapshot
      store.applySnapshot({
        type: "snapshot",
        subscriptionId,
        revision: 1,
        data: [
          { id: "1", name: "Entity 1", value: 10 },
          { id: "2", name: "Entity 2", value: 20 },
        ],
      });
    });

    it("should add new entity on upsert", () => {
      const message: UpsertMessage<TestEntity> = {
        type: "upsert",
        subscriptionId,
        revision: 2,
        data: { id: "3", name: "Entity 3", value: 30 },
      };

      const applied = store.applyUpsert(message);

      expect(applied).toBe(true);
      expect(store.getData()).toHaveLength(3);
      expect(store.getById("3")).toEqual({
        id: "3",
        name: "Entity 3",
        value: 30,
      });
      expect(store.getLastRevision()).toBe(2);
    });

    it("should update existing entity on upsert", () => {
      const message: UpsertMessage<TestEntity> = {
        type: "upsert",
        subscriptionId,
        revision: 2,
        data: { id: "1", name: "Updated Entity 1", value: 100 },
      };

      const applied = store.applyUpsert(message);

      expect(applied).toBe(true);
      expect(store.getData()).toHaveLength(2);
      expect(store.getById("1")).toEqual({
        id: "1",
        name: "Updated Entity 1",
        value: 100,
      });
    });

    it("should reject stale upsert (revision <= lastApplied)", () => {
      const applied = store.applyUpsert({
        type: "upsert",
        subscriptionId,
        revision: 1,
        data: { id: "3", name: "Stale", value: 0 },
      });

      expect(applied).toBe(false);
      expect(store.getById("3")).toBeUndefined();
      expect(store.getLastRevision()).toBe(1);
    });

    it("should apply upserts in revision order", () => {
      // Apply upserts in correct order
      store.applyUpsert({
        type: "upsert",
        subscriptionId,
        revision: 2,
        data: { id: "1", name: "Rev 2", value: 2 },
      });

      store.applyUpsert({
        type: "upsert",
        subscriptionId,
        revision: 3,
        data: { id: "1", name: "Rev 3", value: 3 },
      });

      expect(store.getById("1")?.value).toBe(3);
      expect(store.getLastRevision()).toBe(3);
    });
  });

  describe("delete operations", () => {
    beforeEach(() => {
      store.applySnapshot({
        type: "snapshot",
        subscriptionId,
        revision: 1,
        data: [
          { id: "1", name: "Entity 1", value: 10 },
          { id: "2", name: "Entity 2", value: 20 },
          { id: "3", name: "Entity 3", value: 30 },
        ],
      });
    });

    it("should remove entity on delete", () => {
      const message: DeleteMessage = {
        type: "delete",
        subscriptionId,
        revision: 2,
        id: "2",
      };

      const applied = store.applyDelete(message);

      expect(applied).toBe(true);
      expect(store.getData()).toHaveLength(2);
      expect(store.getById("2")).toBeUndefined();
      expect(store.getLastRevision()).toBe(2);
    });

    it("should handle delete of non-existent entity", () => {
      const message: DeleteMessage = {
        type: "delete",
        subscriptionId,
        revision: 2,
        id: "non-existent",
      };

      const applied = store.applyDelete(message);

      // Should still apply (update revision) but not throw
      expect(applied).toBe(true);
      expect(store.getData()).toHaveLength(3);
      expect(store.getLastRevision()).toBe(2);
    });

    it("should reject stale delete (revision <= lastApplied)", () => {
      const applied = store.applyDelete({
        type: "delete",
        subscriptionId,
        revision: 1,
        id: "2",
      });

      expect(applied).toBe(false);
      expect(store.getById("2")).toBeDefined();
      expect(store.getLastRevision()).toBe(1);
    });
  });

  describe("applyMessage dispatcher", () => {
    beforeEach(() => {
      store.applySnapshot({
        type: "snapshot",
        subscriptionId,
        revision: 1,
        data: [{ id: "1", name: "Entity 1", value: 10 }],
      });
    });

    it("should dispatch snapshot messages", () => {
      const applied = store.applyMessage({
        type: "snapshot",
        subscriptionId,
        revision: 2,
        data: [{ id: "2", name: "New", value: 20 }],
      });

      expect(applied).toBe(true);
      expect(store.getById("2")).toBeDefined();
    });

    it("should dispatch upsert messages", () => {
      const applied = store.applyMessage({
        type: "upsert",
        subscriptionId,
        revision: 2,
        data: { id: "2", name: "Added", value: 20 },
      });

      expect(applied).toBe(true);
      expect(store.getById("2")).toBeDefined();
    });

    it("should dispatch delete messages", () => {
      const applied = store.applyMessage({
        type: "delete",
        subscriptionId,
        revision: 2,
        id: "1",
      });

      expect(applied).toBe(true);
      expect(store.getById("1")).toBeUndefined();
    });

    it("should ignore messages for different subscriptions", () => {
      const applied = store.applyMessage({
        type: "upsert",
        subscriptionId: "different-subscription",
        revision: 2,
        data: { id: "2", name: "Wrong Sub", value: 0 },
      });

      expect(applied).toBe(false);
      expect(store.getById("2")).toBeUndefined();
    });
  });

  describe("error handling", () => {
    it("should set error state", () => {
      const error = new Error("Connection failed");
      store.setError(error);

      expect(store.getError()).toBe(error);
      expect(store.isLoading()).toBe(false);
    });

    it("should clear error on successful snapshot", () => {
      store.setError(new Error("Previous error"));

      store.applySnapshot({
        type: "snapshot",
        subscriptionId,
        revision: 1,
        data: [],
      });

      expect(store.getError()).toBeNull();
    });
  });

  describe("reset", () => {
    it("should reset store to initial state", () => {
      store.applySnapshot({
        type: "snapshot",
        subscriptionId,
        revision: 10,
        data: [{ id: "1", name: "Entity", value: 1 }],
      });

      store.reset();

      expect(store.getData()).toEqual([]);
      expect(store.getLastRevision()).toBe(0);
      expect(store.isLoading()).toBe(true);
      expect(store.getError()).toBeNull();
    });
  });

  describe("subscription listeners", () => {
    it("should notify listeners on data change", () => {
      const listener = vi.fn();
      store.subscribe(listener);

      store.applySnapshot({
        type: "snapshot",
        subscriptionId,
        revision: 1,
        data: [{ id: "1", name: "Entity", value: 1 }],
      });

      expect(listener).toHaveBeenCalledTimes(1);
    });

    it("should unsubscribe listener", () => {
      const listener = vi.fn();
      const unsubscribe = store.subscribe(listener);

      unsubscribe();

      store.applySnapshot({
        type: "snapshot",
        subscriptionId,
        revision: 1,
        data: [],
      });

      expect(listener).not.toHaveBeenCalled();
    });

    it("should not notify on stale updates", () => {
      store.applySnapshot({
        type: "snapshot",
        subscriptionId,
        revision: 5,
        data: [],
      });

      const listener = vi.fn();
      store.subscribe(listener);

      store.applySnapshot({
        type: "snapshot",
        subscriptionId,
        revision: 3,
        data: [],
      });

      expect(listener).not.toHaveBeenCalled();
    });
  });
});
