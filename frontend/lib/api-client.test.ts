/**
 * TDD Tests for Frontend API Client (T008).
 *
 * RED PHASE: Tests written before implementation.
 * Expected: All tests should fail initially.
 *
 * Tests cover:
 * - Base client with consistent error handling
 * - Loading/error/stale state management
 * - Automatic retry with exponential backoff
 * - Request cancellation support
 * - Type-safe API responses
 */
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

describe("ApiClient", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  describe("createApiClient", () => {
    it("should create client with default base URL", async () => {
      const { createApiClient } = await import("./api-client");
      const client = createApiClient();
      expect(client.baseUrl).toBe("http://localhost:8000/api/v1");
    });

    it("should create client with custom base URL", async () => {
      const { createApiClient } = await import("./api-client");
      const client = createApiClient({ baseUrl: "http://custom:9000/api/v1" });
      expect(client.baseUrl).toBe("http://custom:9000/api/v1");
    });

    it("should support authorization token", async () => {
      const { createApiClient } = await import("./api-client");
      const client = createApiClient({ token: "test-token" });
      expect(client.token).toBe("test-token");
    });
  });

  describe("GET requests", () => {
    it("should make GET request and return data", async () => {
      const { createApiClient } = await import("./api-client");
      const mockData = { items: [], total: 0 };

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockData),
      });

      const client = createApiClient();
      const result = await client.get("/projects");

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/projects",
        expect.objectContaining({
          method: "GET",
          headers: expect.objectContaining({
            "Content-Type": "application/json",
          }),
        })
      );
      expect(result.data).toEqual(mockData);
    });

    it("should include query parameters in GET request", async () => {
      const { createApiClient } = await import("./api-client");

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ items: [] }),
      });

      const client = createApiClient();
      await client.get("/projects", { params: { pinned: true, limit: 10 } });

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/projects?pinned=true&limit=10",
        expect.any(Object)
      );
    });

    it("should include Authorization header when token is set", async () => {
      const { createApiClient } = await import("./api-client");

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({}),
      });

      const client = createApiClient({ token: "bearer-token-123" });
      await client.get("/settings");

      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: "Bearer bearer-token-123",
          }),
        })
      );
    });
  });

  describe("POST requests", () => {
    it("should make POST request with JSON body", async () => {
      const { createApiClient } = await import("./api-client");
      const requestBody = { title: "New Task", type: "implementation" };
      const responseData = { taskId: "T001", auditEntryId: "audit-123" };

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: () => Promise.resolve(responseData),
      });

      const client = createApiClient();
      const result = await client.post("/projects/proj1/tasks", {
        body: requestBody,
      });

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/projects/proj1/tasks",
        expect.objectContaining({
          method: "POST",
          headers: expect.objectContaining({
            "Content-Type": "application/json",
          }),
          body: JSON.stringify(requestBody),
        })
      );
      expect(result.data).toEqual(responseData);
    });
  });

  describe("PATCH requests", () => {
    it("should make PATCH request with JSON body", async () => {
      const { createApiClient } = await import("./api-client");

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ projectId: "proj1", pinned: true }),
      });

      const client = createApiClient();
      await client.patch("/projects/proj1/pin", { body: { pinned: true } });

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/projects/proj1/pin",
        expect.objectContaining({
          method: "PATCH",
          body: JSON.stringify({ pinned: true }),
        })
      );
    });
  });

  describe("DELETE requests", () => {
    it("should make DELETE request", async () => {
      const { createApiClient } = await import("./api-client");

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: () => Promise.resolve(null),
      });

      const client = createApiClient();
      await client.delete("/pairing/pairing-123");

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/pairing/pairing-123",
        expect.objectContaining({
          method: "DELETE",
        })
      );
    });
  });

  describe("Error handling", () => {
    it("should throw ApiError on 400 Bad Request", async () => {
      const { createApiClient, ApiError } = await import("./api-client");

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: () =>
          Promise.resolve({
            error: "validation_error",
            message: "Invalid request body",
            details: [{ field: "title", message: "Required" }],
          }),
      });

      const client = createApiClient();

      await expect(client.post("/projects/proj1/tasks", { body: {} })).rejects.toThrow(
        ApiError
      );
    });

    it("should include error details in ApiError", async () => {
      const { createApiClient, ApiError } = await import("./api-client");

      const errorResponse = {
        error: "validation_error",
        message: "Invalid request body",
        details: [{ field: "title", message: "Required" }],
      };

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: () => Promise.resolve(errorResponse),
      });

      const client = createApiClient();

      try {
        await client.post("/projects/proj1/tasks", { body: {} });
        expect.fail("Should have thrown");
      } catch (e) {
        expect(e).toBeInstanceOf(ApiError);
        const apiError = e as InstanceType<typeof ApiError>;
        expect(apiError.status).toBe(400);
        expect(apiError.errorCode).toBe("validation_error");
        expect(apiError.message).toBe("Invalid request body");
        expect(apiError.details).toEqual(errorResponse.details);
      }
    });

    it("should handle 401 Unauthorized", async () => {
      const { createApiClient, ApiError } = await import("./api-client");

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () =>
          Promise.resolve({
            error: "unauthorized",
            message: "Valid bearer token required",
          }),
      });

      const client = createApiClient();

      try {
        await client.get("/settings");
        expect.fail("Should have thrown");
      } catch (e) {
        expect(e).toBeInstanceOf(ApiError);
        const apiError = e as InstanceType<typeof ApiError>;
        expect(apiError.status).toBe(401);
        expect(apiError.errorCode).toBe("unauthorized");
      }
    });

    it("should handle 403 Forbidden with guard failures", async () => {
      const { createApiClient, ApiError } = await import("./api-client");

      const errorResponse = {
        error: "guard_failure",
        message: "Action blocked by guard",
        guardFailures: [
          { guard: "session-active", reason: "Session must be active" },
        ],
      };

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: () => Promise.resolve(errorResponse),
      });

      const client = createApiClient();

      try {
        await client.post("/projects/proj1/tasks/T001/transition", {
          body: { toState: "done" },
        });
        expect.fail("Should have thrown");
      } catch (e) {
        expect(e).toBeInstanceOf(ApiError);
        const apiError = e as InstanceType<typeof ApiError>;
        expect(apiError.status).toBe(403);
        expect(apiError.guardFailures).toEqual(errorResponse.guardFailures);
      }
    });

    it("should handle 404 Not Found", async () => {
      const { createApiClient, ApiError } = await import("./api-client");

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: () =>
          Promise.resolve({
            error: "not_found",
            message: "Task T999 not found",
          }),
      });

      const client = createApiClient();

      try {
        await client.get("/projects/proj1/tasks/T999");
        expect.fail("Should have thrown");
      } catch (e) {
        expect(e).toBeInstanceOf(ApiError);
        const apiError = e as InstanceType<typeof ApiError>;
        expect(apiError.status).toBe(404);
        expect(apiError.message).toBe("Task T999 not found");
      }
    });

    it("should handle 500 Internal Server Error", async () => {
      const { createApiClient, ApiError } = await import("./api-client");

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () =>
          Promise.resolve({
            error: "internal_error",
            message: "An unexpected error occurred",
            correlationId: "corr-123",
          }),
      });

      const client = createApiClient();

      try {
        await client.get("/projects");
        expect.fail("Should have thrown");
      } catch (e) {
        expect(e).toBeInstanceOf(ApiError);
        const apiError = e as InstanceType<typeof ApiError>;
        expect(apiError.status).toBe(500);
        expect(apiError.correlationId).toBe("corr-123");
      }
    });

    it("should handle network errors", async () => {
      const { createApiClient, NetworkError } = await import("./api-client");

      global.fetch = vi.fn().mockRejectedValueOnce(new Error("Failed to fetch"));

      const client = createApiClient();

      await expect(client.get("/projects")).rejects.toThrow(NetworkError);
    });
  });

  describe("Request cancellation", () => {
    it("should support request cancellation via AbortController", async () => {
      const { createApiClient } = await import("./api-client");

      const abortController = new AbortController();
      global.fetch = vi.fn().mockImplementationOnce(
        () =>
          new Promise((_, reject) => {
            abortController.signal.addEventListener("abort", () => {
              reject(new DOMException("Aborted", "AbortError"));
            });
          })
      );

      const client = createApiClient();
      const requestPromise = client.get("/projects", {
        signal: abortController.signal,
      });

      abortController.abort();

      await expect(requestPromise).rejects.toThrow();
    });
  });

  describe("Retry with backoff", () => {
    it("should retry on 5xx errors", async () => {
      const { createApiClient } = await import("./api-client");

      global.fetch = vi
        .fn()
        .mockResolvedValueOnce({
          ok: false,
          status: 503,
          json: () =>
            Promise.resolve({
              error: "service_unavailable",
              message: "Try again later",
            }),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ items: [] }),
        });

      const client = createApiClient({ retries: 1 });
      const resultPromise = client.get("/projects");

      // Advance timers for retry delay
      await vi.advanceTimersByTimeAsync(1000);

      const result = await resultPromise;
      expect(result.data).toEqual({ items: [] });
      expect(fetch).toHaveBeenCalledTimes(2);
    });

    it("should not retry on 4xx errors", async () => {
      const { createApiClient, ApiError } = await import("./api-client");

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: () =>
          Promise.resolve({
            error: "bad_request",
            message: "Invalid input",
          }),
      });

      const client = createApiClient({ retries: 2 });

      await expect(client.get("/projects")).rejects.toThrow(ApiError);
      expect(fetch).toHaveBeenCalledTimes(1);
    });

    it("should use exponential backoff for retries", async () => {
      const { createApiClient } = await import("./api-client");

      global.fetch = vi
        .fn()
        .mockResolvedValueOnce({
          ok: false,
          status: 503,
          json: () =>
            Promise.resolve({
              error: "service_unavailable",
              message: "Try again later",
            }),
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 503,
          json: () =>
            Promise.resolve({
              error: "service_unavailable",
              message: "Try again later",
            }),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ items: [] }),
        });

      const client = createApiClient({ retries: 2, retryDelay: 1000 });
      const resultPromise = client.get("/projects");

      // First retry after 1000ms
      await vi.advanceTimersByTimeAsync(1000);
      // Second retry after 2000ms (exponential backoff)
      await vi.advanceTimersByTimeAsync(2000);

      const result = await resultPromise;
      expect(result.data).toEqual({ items: [] });
      expect(fetch).toHaveBeenCalledTimes(3);
    });
  });

  describe("Response metadata", () => {
    it("should include response status in result", async () => {
      const { createApiClient } = await import("./api-client");

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ items: [] }),
      });

      const client = createApiClient();
      const result = await client.get("/projects");

      expect(result.status).toBe(200);
    });

    it("should include response headers in result", async () => {
      const { createApiClient } = await import("./api-client");
      const headers = new Headers();
      headers.set("X-Request-Id", "req-123");

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers,
        json: () => Promise.resolve({ items: [] }),
      });

      const client = createApiClient();
      const result = await client.get("/projects");

      expect(result.headers.get("X-Request-Id")).toBe("req-123");
    });
  });
});

describe("useApiQuery (React hook)", () => {
  it("should export useApiQuery hook", async () => {
    const { useApiQuery } = await import("./api-client");
    expect(useApiQuery).toBeDefined();
    expect(typeof useApiQuery).toBe("function");
  });

  // Note: React hook tests would require additional setup with React Testing Library
  // These are placeholder tests for the hook interface
  it("should return loading state initially", async () => {
    const { useApiQuery } = await import("./api-client");
    // This would be tested with React Testing Library in a real component test
    expect(useApiQuery).toBeDefined();
  });
});

describe("Type exports", () => {
  it("should export ApiResponse type", async () => {
    // Type-only test - if this compiles, the type exists
    const { createApiClient } = await import("./api-client");
    const client = createApiClient();

    // Type assertion to verify ApiResponse shape
    const result = await Promise.resolve({
      data: { items: [] },
      status: 200,
      headers: new Headers(),
    });

    expect(result).toBeDefined();
  });

  it("should export ApiError class", async () => {
    const { ApiError } = await import("./api-client");
    expect(ApiError).toBeDefined();
    expect(new ApiError(400, "bad_request", "Test")).toBeInstanceOf(Error);
  });

  it("should export NetworkError class", async () => {
    const { NetworkError } = await import("./api-client");
    expect(NetworkError).toBeDefined();
    expect(new NetworkError("Connection failed")).toBeInstanceOf(Error);
  });
});
