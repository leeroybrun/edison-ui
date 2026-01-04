import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { EntityAuditPanel } from "./EntityAuditPanel";

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

const mockActivityResponse = {
  items: [
    {
      timestamp: "2025-12-27T10:00:00Z",
      eventType: "task.transition",
      summary: "Task T005 moved to done",
      sessionId: "session-1",
      taskId: "T005",
      invocationId: "inv-123",
      actor: {
        osUser: "leeroy",
        displayName: "Leeroy Jenkins",
      },
    },
    {
      timestamp: "2025-12-27T09:00:00Z",
      eventType: "task.create",
      summary: "Task T005 created",
      sessionId: null,
      taskId: "T005",
      invocationId: "inv-121",
      actor: {
        osUser: "system",
        displayName: "System",
      },
    },
  ],
  hasMore: false,
};

describe("EntityAuditPanel", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders panel with entity title for task", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockActivityResponse),
    });

    render(
      <EntityAuditPanel
        entityType="task"
        entityId="T005"
        projectId="project-1"
      />
    );

    // Panel title includes entity ID and "Activity"
    expect(screen.getByText(/Task T005 Activity/)).toBeInTheDocument();
  });

  it("renders panel with entity title for session", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockActivityResponse),
    });

    render(
      <EntityAuditPanel
        entityType="session"
        entityId="session-1"
        projectId="project-1"
      />
    );

    expect(screen.getByText(/session-1/)).toBeInTheDocument();
  });

  it("fetches activity filtered by entity", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockActivityResponse),
    });

    render(
      <EntityAuditPanel
        entityType="task"
        entityId="T005"
        projectId="project-1"
      />
    );

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("taskId=T005"),
        expect.any(Object)
      );
    });
  });

  it("fetches activity filtered by session when entityType is session", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockActivityResponse),
    });

    render(
      <EntityAuditPanel
        entityType="session"
        entityId="session-1"
        projectId="project-1"
      />
    );

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("sessionId=session-1"),
        expect.any(Object)
      );
    });
  });

  it("displays loading state while fetching", () => {
    mockFetch.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(
      <EntityAuditPanel
        entityType="task"
        entityId="T005"
        projectId="project-1"
      />
    );

    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("displays activity items after loading", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockActivityResponse),
    });

    render(
      <EntityAuditPanel
        entityType="task"
        entityId="T005"
        projectId="project-1"
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Task T005 moved to done")).toBeInTheDocument();
    });
  });

  it("shows error state when fetch fails", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    render(
      <EntityAuditPanel
        entityType="task"
        entityId="T005"
        projectId="project-1"
      />
    );

    await waitFor(() => {
      // Specific error message shown
      expect(screen.getByText("Error loading activity")).toBeInTheDocument();
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });

  it("is collapsible", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockActivityResponse),
    });

    render(
      <EntityAuditPanel
        entityType="task"
        entityId="T005"
        projectId="project-1"
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Task T005 moved to done")).toBeInTheDocument();
    });

    // Find collapse button
    const collapseButton = screen.getByRole("button", { name: /collapse|toggle|expand/i });
    expect(collapseButton).toBeInTheDocument();

    // Click to collapse
    fireEvent.click(collapseButton);

    // Content should be hidden
    await waitFor(() => {
      expect(screen.queryByText("Task T005 moved to done")).not.toBeInTheDocument();
    });
  });

  it("shows empty state when no activity for entity", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ items: [], hasMore: false }),
    });

    render(
      <EntityAuditPanel
        entityType="task"
        entityId="T005"
        projectId="project-1"
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/no activity/i)).toBeInTheDocument();
    });
  });

  it("has accessible heading structure", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockActivityResponse),
    });

    render(
      <EntityAuditPanel
        entityType="task"
        entityId="T005"
        projectId="project-1"
      />
    );

    // Should have a heading for the panel
    expect(screen.getByRole("heading")).toBeInTheDocument();
  });
});
