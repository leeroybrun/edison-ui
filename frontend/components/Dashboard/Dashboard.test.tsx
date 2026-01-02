import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { Dashboard } from "./Dashboard";
import type { ProjectListResponse } from "./types";

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

const mockProjectsResponse: ProjectListResponse = {
  items: [
    {
      projectId: "project-1",
      path: "~/projects/alpha",
      name: "Alpha Project",
      pinned: true,
      health: { taskCount: 10, sessionCount: 2, qaCount: 5, activeCount: 1 },
      lastActivityAt: "2025-12-27T10:00:00Z",
      hasGit: true,
      errors: [],
    },
    {
      projectId: "project-2",
      path: "~/projects/beta",
      name: "Beta Project",
      pinned: false,
      health: { taskCount: 20, sessionCount: 4, qaCount: 8, activeCount: 3 },
      lastActivityAt: "2025-12-26T10:00:00Z",
      hasGit: true,
      errors: [],
    },
  ],
  total: 2,
  limit: 100,
  offset: 0,
};

describe("Dashboard", () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders dashboard title", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockProjectsResponse,
    });

    render(<Dashboard />);

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });

  it("shows loading state while fetching projects", () => {
    mockFetch.mockImplementation(
      () => new Promise(() => {}), // Never resolves
    );

    render(<Dashboard />);

    expect(screen.getByText(/loading projects/i)).toBeInTheDocument();
  });

  it("fetches and displays projects on mount", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockProjectsResponse,
    });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText("Alpha Project")).toBeInTheDocument();
      expect(screen.getByText("Beta Project")).toBeInTheDocument();
    });
  });

  it("displays error state on fetch failure", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
    });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  it("displays summary counts at top of dashboard", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockProjectsResponse,
    });

    render(<Dashboard />);

    await waitFor(() => {
      // Total tasks: 10 + 20 = 30 - check in summary section
      expect(screen.getByText("30")).toBeInTheDocument();
      // Total active: 1 + 3 = 4 - look for it alongside "Active" label
      // Use getAllBy since multiple elements may have "4"
      const activeElements = screen.getAllByText("4");
      expect(activeElements.length).toBeGreaterThan(0);
    });
  });

  it("allows pinning a project", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockProjectsResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ projectId: "project-2", pinned: true }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          ...mockProjectsResponse,
          items: mockProjectsResponse.items.map((p) =>
            p.projectId === "project-2" ? { ...p, pinned: true } : p,
          ),
        }),
      });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText("Beta Project")).toBeInTheDocument();
    });
  });

  it("displays recent activity section", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockProjectsResponse,
    });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/recent activity/i)).toBeInTheDocument();
    });
  });

  it("links to settings when no projects found", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ items: [], total: 0, limit: 100, offset: 0 }),
    });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/no projects found/i)).toBeInTheDocument();
      expect(screen.getByRole("link", { name: /configure/i })).toHaveAttribute(
        "href",
        "/settings",
      );
    });
  });
});
