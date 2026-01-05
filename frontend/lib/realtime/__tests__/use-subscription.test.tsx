/**
 * Tests for useSubscription hook
 *
 * TDD RED phase: These tests define expected behavior before implementation.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useSubscription } from "../use-subscription";
import type { Entity } from "../types";

interface TestTask extends Entity {
  id: string;
  title: string;
  state: string;
}

// Mock WebSocket
class MockWebSocket {
  static instances: MockWebSocket[] = [];
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  url: string;
  readyState: number = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  sentMessages: string[] = [];
  private openTimeout: ReturnType<typeof setTimeout> | null = null;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
    // Simulate async connection with a short delay
    this.openTimeout = setTimeout(() => this.simulateOpen(), 10);
  }

  send(data: string): void {
    this.sentMessages.push(data);
  }

  close(): void {
    if (this.openTimeout) {
      clearTimeout(this.openTimeout);
      this.openTimeout = null;
    }
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent("close"));
    }
  }

  simulateOpen(): void {
    if (this.readyState === MockWebSocket.CLOSED) return;
    this.readyState = MockWebSocket.OPEN;
    if (this.onopen) {
      this.onopen(new Event("open"));
    }
  }

  simulateMessage<T>(data: T): void {
    if (this.onmessage) {
      this.onmessage(
        new MessageEvent("message", { data: JSON.stringify(data) }),
      );
    }
  }

  simulateError(): void {
    if (this.onerror) {
      this.onerror(new Event("error"));
    }
  }

  static getLastInstance(): MockWebSocket | undefined {
    return MockWebSocket.instances[MockWebSocket.instances.length - 1];
  }

  static clearInstances(): void {
    // Clean up any pending timeouts
    for (const instance of MockWebSocket.instances) {
      if (instance.openTimeout) {
        clearTimeout(instance.openTimeout);
      }
    }
    MockWebSocket.instances = [];
  }
}

// Replace global WebSocket
const originalWebSocket = global.WebSocket;

describe("useSubscription", () => {
  beforeEach(() => {
    MockWebSocket.clearInstances();
    // Use type assertion to mock global WebSocket for tests
    (global as unknown as { WebSocket: typeof MockWebSocket }).WebSocket =
      MockWebSocket;
  });

  afterEach(() => {
    global.WebSocket = originalWebSocket;
    vi.clearAllMocks();
  });

  describe("initial state", () => {
    it("should return loading state initially", () => {
      const { result } = renderHook(() =>
        useSubscription<TestTask>("tasks", { projectId: "proj-1" }),
      );

      expect(result.current.isLoading).toBe(true);
      expect(result.current.data).toEqual([]);
      expect(result.current.error).toBeNull();
      expect(result.current.revision).toBe(0);
    });

    it("should establish WebSocket connection on mount", async () => {
      renderHook(() => useSubscription<TestTask>("tasks"));

      await waitFor(() => {
        expect(MockWebSocket.instances).toHaveLength(1);
      });
    });
  });

  describe("subscription lifecycle", () => {
    it("should send subscribe message after connection opens", async () => {
      renderHook(() =>
        useSubscription<TestTask>("tasks", { projectId: "proj-1" }),
      );

      // Wait for connection to open
      let ws: MockWebSocket | undefined;
      await waitFor(
        () => {
          ws = MockWebSocket.getLastInstance();
          expect(ws?.readyState).toBe(MockWebSocket.OPEN);
        },
        { timeout: 2000 },
      );

      // Wait a bit for the subscribe message to be sent
      await waitFor(
        () => {
          expect(ws?.sentMessages.length).toBeGreaterThan(0);
        },
        { timeout: 2000 },
      );

      expect(ws).toBeDefined();
      expect(ws!.sentMessages.length).toBeGreaterThan(0);

      const subscribeMessage = JSON.parse(ws!.sentMessages[0]);

      expect(subscribeMessage.type).toBe("subscribe");
      expect(subscribeMessage.resource).toBe("tasks");
      expect(subscribeMessage.params).toEqual({ projectId: "proj-1" });
      expect(subscribeMessage.subscriptionId).toBeDefined();
    });

    it("should send unsubscribe message on unmount", async () => {
      const { unmount } = renderHook(() => useSubscription<TestTask>("tasks"));

      await waitFor(() => {
        const ws = MockWebSocket.getLastInstance();
        expect(ws?.readyState).toBe(MockWebSocket.OPEN);
      });

      const ws = MockWebSocket.getLastInstance();
      const subscribeMessage = JSON.parse(ws!.sentMessages[0]);
      const subscriptionId = subscribeMessage.subscriptionId;

      unmount();

      // Should send unsubscribe
      const lastMessage = JSON.parse(
        ws!.sentMessages[ws!.sentMessages.length - 1],
      );
      expect(lastMessage.type).toBe("unsubscribe");
      expect(lastMessage.subscriptionId).toBe(subscriptionId);
    });
  });

  describe("snapshot handling", () => {
    it("should update data on snapshot message", async () => {
      const { result } = renderHook(() => useSubscription<TestTask>("tasks"));

      await waitFor(() => {
        const ws = MockWebSocket.getLastInstance();
        expect(ws?.readyState).toBe(MockWebSocket.OPEN);
      });

      const ws = MockWebSocket.getLastInstance();
      const subscribeMessage = JSON.parse(ws!.sentMessages[0]);

      act(() => {
        ws!.simulateMessage({
          type: "snapshot",
          subscriptionId: subscribeMessage.subscriptionId,
          revision: 1,
          data: [
            { id: "task-1", title: "Task 1", state: "todo" },
            { id: "task-2", title: "Task 2", state: "wip" },
          ],
        });
      });

      await waitFor(() => {
        expect(result.current.data).toHaveLength(2);
      });

      expect(result.current.isLoading).toBe(false);
      expect(result.current.revision).toBe(1);
      expect(result.current.data[0].id).toBe("task-1");
    });
  });

  describe("upsert handling", () => {
    it("should add entity on upsert message", async () => {
      const { result } = renderHook(() => useSubscription<TestTask>("tasks"));

      await waitFor(() => {
        const ws = MockWebSocket.getLastInstance();
        expect(ws?.readyState).toBe(MockWebSocket.OPEN);
      });

      const ws = MockWebSocket.getLastInstance();
      const subscribeMessage = JSON.parse(ws!.sentMessages[0]);

      // First send a snapshot
      act(() => {
        ws!.simulateMessage({
          type: "snapshot",
          subscriptionId: subscribeMessage.subscriptionId,
          revision: 1,
          data: [{ id: "task-1", title: "Task 1", state: "todo" }],
        });
      });

      await waitFor(() => {
        expect(result.current.data).toHaveLength(1);
      });

      // Then send an upsert
      act(() => {
        ws!.simulateMessage({
          type: "upsert",
          subscriptionId: subscribeMessage.subscriptionId,
          revision: 2,
          data: { id: "task-2", title: "Task 2", state: "wip" },
        });
      });

      await waitFor(() => {
        expect(result.current.data).toHaveLength(2);
      });

      expect(result.current.revision).toBe(2);
    });

    it("should update existing entity on upsert message", async () => {
      const { result } = renderHook(() => useSubscription<TestTask>("tasks"));

      await waitFor(() => {
        const ws = MockWebSocket.getLastInstance();
        expect(ws?.readyState).toBe(MockWebSocket.OPEN);
      });

      const ws = MockWebSocket.getLastInstance();
      const subscribeMessage = JSON.parse(ws!.sentMessages[0]);

      act(() => {
        ws!.simulateMessage({
          type: "snapshot",
          subscriptionId: subscribeMessage.subscriptionId,
          revision: 1,
          data: [{ id: "task-1", title: "Task 1", state: "todo" }],
        });
      });

      await waitFor(() => {
        expect(result.current.data).toHaveLength(1);
      });

      act(() => {
        ws!.simulateMessage({
          type: "upsert",
          subscriptionId: subscribeMessage.subscriptionId,
          revision: 2,
          data: { id: "task-1", title: "Updated Task 1", state: "wip" },
        });
      });

      await waitFor(() => {
        expect(result.current.data[0].title).toBe("Updated Task 1");
      });

      expect(result.current.data).toHaveLength(1);
      expect(result.current.data[0].state).toBe("wip");
    });
  });

  describe("delete handling", () => {
    it("should remove entity on delete message", async () => {
      const { result } = renderHook(() => useSubscription<TestTask>("tasks"));

      await waitFor(() => {
        const ws = MockWebSocket.getLastInstance();
        expect(ws?.readyState).toBe(MockWebSocket.OPEN);
      });

      const ws = MockWebSocket.getLastInstance();
      const subscribeMessage = JSON.parse(ws!.sentMessages[0]);

      act(() => {
        ws!.simulateMessage({
          type: "snapshot",
          subscriptionId: subscribeMessage.subscriptionId,
          revision: 1,
          data: [
            { id: "task-1", title: "Task 1", state: "todo" },
            { id: "task-2", title: "Task 2", state: "wip" },
          ],
        });
      });

      await waitFor(() => {
        expect(result.current.data).toHaveLength(2);
      });

      act(() => {
        ws!.simulateMessage({
          type: "delete",
          subscriptionId: subscribeMessage.subscriptionId,
          revision: 2,
          id: "task-1",
        });
      });

      await waitFor(() => {
        expect(result.current.data).toHaveLength(1);
      });

      expect(result.current.data[0].id).toBe("task-2");
      expect(result.current.revision).toBe(2);
    });
  });

  describe("revision ordering", () => {
    it("should ignore stale updates (revision <= lastApplied)", async () => {
      const { result } = renderHook(() => useSubscription<TestTask>("tasks"));

      await waitFor(() => {
        const ws = MockWebSocket.getLastInstance();
        expect(ws?.readyState).toBe(MockWebSocket.OPEN);
      });

      const ws = MockWebSocket.getLastInstance();
      const subscribeMessage = JSON.parse(ws!.sentMessages[0]);

      // Apply snapshot at revision 5
      act(() => {
        ws!.simulateMessage({
          type: "snapshot",
          subscriptionId: subscribeMessage.subscriptionId,
          revision: 5,
          data: [{ id: "task-1", title: "Current", state: "todo" }],
        });
      });

      await waitFor(() => {
        expect(result.current.revision).toBe(5);
      });

      // Try to apply stale upsert at revision 3
      act(() => {
        ws!.simulateMessage({
          type: "upsert",
          subscriptionId: subscribeMessage.subscriptionId,
          revision: 3,
          data: { id: "task-1", title: "Stale Update", state: "stale" },
        });
      });

      // Data should not change
      expect(result.current.data[0].title).toBe("Current");
      expect(result.current.revision).toBe(5);
    });

    it("should apply updates in revision order", async () => {
      const { result } = renderHook(() => useSubscription<TestTask>("tasks"));

      await waitFor(() => {
        const ws = MockWebSocket.getLastInstance();
        expect(ws?.readyState).toBe(MockWebSocket.OPEN);
      });

      const ws = MockWebSocket.getLastInstance();
      const subscribeMessage = JSON.parse(ws!.sentMessages[0]);

      act(() => {
        ws!.simulateMessage({
          type: "snapshot",
          subscriptionId: subscribeMessage.subscriptionId,
          revision: 1,
          data: [{ id: "task-1", title: "Initial", state: "todo" }],
        });
      });

      await waitFor(() => {
        expect(result.current.revision).toBe(1);
      });

      // Apply updates in order
      act(() => {
        ws!.simulateMessage({
          type: "upsert",
          subscriptionId: subscribeMessage.subscriptionId,
          revision: 2,
          data: { id: "task-1", title: "Update 2", state: "wip" },
        });
      });

      act(() => {
        ws!.simulateMessage({
          type: "upsert",
          subscriptionId: subscribeMessage.subscriptionId,
          revision: 3,
          data: { id: "task-1", title: "Update 3", state: "done" },
        });
      });

      await waitFor(() => {
        expect(result.current.revision).toBe(3);
      });

      expect(result.current.data[0].title).toBe("Update 3");
      expect(result.current.data[0].state).toBe("done");
    });
  });

  describe("connection state", () => {
    it("should expose isConnected state", async () => {
      const { result } = renderHook(() => useSubscription<TestTask>("tasks"));

      // Initially not connected
      expect(result.current.isConnected).toBe(false);

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });
    });
  });

  describe("error handling", () => {
    it("should set error on error message", async () => {
      const { result } = renderHook(() => useSubscription<TestTask>("tasks"));

      await waitFor(() => {
        const ws = MockWebSocket.getLastInstance();
        expect(ws?.readyState).toBe(MockWebSocket.OPEN);
      });

      const ws = MockWebSocket.getLastInstance();
      const subscribeMessage = JSON.parse(ws!.sentMessages[0]);

      act(() => {
        ws!.simulateMessage({
          type: "error",
          subscriptionId: subscribeMessage.subscriptionId,
          code: "INVALID_RESOURCE",
          message: "Resource not found",
        });
      });

      await waitFor(() => {
        expect(result.current.error).not.toBeNull();
      });

      expect(result.current.error?.message).toContain("Resource not found");
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe("params change", () => {
    it("should resubscribe when params change", async () => {
      const { rerender } = renderHook(
        ({ params }: { params?: Record<string, unknown> }) =>
          useSubscription<TestTask>("tasks", params),
        { initialProps: { params: { projectId: "proj-1" } } },
      );

      // Wait for first connection
      await waitFor(
        () => {
          const ws = MockWebSocket.getLastInstance();
          expect(ws?.readyState).toBe(MockWebSocket.OPEN);
          expect(ws?.sentMessages.length).toBeGreaterThan(0);
        },
        { timeout: 2000 },
      );

      const firstWs = MockWebSocket.getLastInstance();
      expect(firstWs).toBeDefined();
      const initialSubscribeMsg = JSON.parse(firstWs!.sentMessages[0]);
      expect(initialSubscribeMsg.params).toEqual({ projectId: "proj-1" });

      const instanceCountBefore = MockWebSocket.instances.length;

      // Change params - this will create a new connection
      rerender({ params: { projectId: "proj-2" } });

      // Wait for new connection to be established
      await waitFor(
        () => {
          expect(MockWebSocket.instances.length).toBeGreaterThan(
            instanceCountBefore,
          );
        },
        { timeout: 2000 },
      );

      // The old connection should have sent an unsubscribe before closing
      expect(firstWs!.sentMessages.length).toBeGreaterThanOrEqual(2);
      const unsubscribeMsg = JSON.parse(
        firstWs!.sentMessages[firstWs!.sentMessages.length - 1],
      );
      expect(unsubscribeMsg.type).toBe("unsubscribe");

      // Wait for new connection to send subscribe
      await waitFor(
        () => {
          const newWs = MockWebSocket.getLastInstance();
          expect(newWs).not.toBe(firstWs);
          expect(newWs?.readyState).toBe(MockWebSocket.OPEN);
          expect(newWs?.sentMessages.length).toBeGreaterThan(0);
        },
        { timeout: 2000 },
      );

      // New connection should have subscribed with new params
      const newWs = MockWebSocket.getLastInstance();
      expect(newWs).not.toBe(firstWs);
      const newSubscribeMsg = JSON.parse(newWs!.sentMessages[0]);
      expect(newSubscribeMsg.type).toBe("subscribe");
      expect(newSubscribeMsg.params).toEqual({ projectId: "proj-2" });
    });
  });
});
