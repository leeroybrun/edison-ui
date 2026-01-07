import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { SessionContextPanel } from "./SessionContextPanel";

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

const mockContextResponse = {
  isEdisonProject: true,
  projectRoot: "[REDACTED]",
  sessionId: "happy-pid-12345",
  sessionState: "active",
  worktreePath: "[REDACTED]/worktrees/happy-pid-12345",
  currentTaskId: "T042",
  currentTaskState: "wip",
  activePacks: ["typescript", "nextjs", "vitest"],
  constitutions: {
    AGENTS: ".edison/_generated/constitutions/AGENTS.md",
    ORCHESTRATORS: ".edison/_generated/constitutions/ORCHESTRATORS.md",
  },
  timestamp: "2025-12-28T15:30:00Z",
};

describe("SessionContextPanel", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it("renders loading state initially", () => {
    mockFetch.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(
      <SessionContextPanel projectId="my-project" sessionId="happy-pid-12345" />
    );

    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders error state when fetch fails", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    render(
      <SessionContextPanel projectId="my-project" sessionId="happy-pid-12345" />
    );

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(screen.getByText(/failed to load session context/i)).toBeInTheDocument();
  });

  it("renders context data in markdown view by default", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockContextResponse),
    });

    render(
      <SessionContextPanel projectId="my-project" sessionId="happy-pid-12345" />
    );

    await waitFor(() => {
      expect(screen.getByText("Session State")).toBeInTheDocument();
    });

    expect(screen.getByText("active")).toBeInTheDocument();
    expect(screen.getByText("T042")).toBeInTheDocument();
    expect(screen.getByText("typescript")).toBeInTheDocument();
    expect(screen.getByText("nextjs")).toBeInTheDocument();
  });

  it("displays active packs as a list", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockContextResponse),
    });

    render(
      <SessionContextPanel projectId="my-project" sessionId="happy-pid-12345" />
    );

    await waitFor(() => {
      expect(screen.getByText("Active Packs")).toBeInTheDocument();
    });

    expect(screen.getByText("typescript")).toBeInTheDocument();
    expect(screen.getByText("nextjs")).toBeInTheDocument();
    expect(screen.getByText("vitest")).toBeInTheDocument();
  });

  it("displays constitutions as name-path pairs", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockContextResponse),
    });

    render(
      <SessionContextPanel projectId="my-project" sessionId="happy-pid-12345" />
    );

    await waitFor(() => {
      expect(screen.getByText("Constitutions")).toBeInTheDocument();
    });

    // Constitution names should be displayed as labels
    expect(screen.getByText("AGENTS:")).toBeInTheDocument();
    expect(screen.getByText("ORCHESTRATORS:")).toBeInTheDocument();
  });

  it("shows redacted paths safely", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockContextResponse),
    });

    render(
      <SessionContextPanel projectId="my-project" sessionId="happy-pid-12345" />
    );

    await waitFor(() => {
      // Multiple elements may contain [REDACTED], use getAllBy
      const redactedElements = screen.getAllByText(/\[REDACTED\]/);
      expect(redactedElements.length).toBeGreaterThan(0);
    });
  });

  it("toggles to JSON view when button is clicked", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockContextResponse),
    });

    render(
      <SessionContextPanel projectId="my-project" sessionId="happy-pid-12345" />
    );

    await waitFor(() => {
      expect(screen.getByText("Session State")).toBeInTheDocument();
    });

    const jsonToggle = screen.getByRole("button", { name: /json/i });
    fireEvent.click(jsonToggle);

    await waitFor(() => {
      expect(screen.getByRole("code")).toBeInTheDocument();
    });
    expect(screen.getByText(/"isEdisonProject"/)).toBeInTheDocument();
  });

  it("toggles back to markdown view from JSON", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockContextResponse),
    });

    render(
      <SessionContextPanel projectId="my-project" sessionId="happy-pid-12345" />
    );

    await waitFor(() => {
      expect(screen.getByText("Session State")).toBeInTheDocument();
    });

    // Toggle to JSON
    const jsonToggle = screen.getByRole("button", { name: /json/i });
    fireEvent.click(jsonToggle);

    await waitFor(() => {
      expect(screen.getByRole("code")).toBeInTheDocument();
    });

    // Toggle back to Markdown
    const markdownToggle = screen.getByRole("button", { name: /markdown/i });
    fireEvent.click(markdownToggle);

    await waitFor(() => {
      expect(screen.getByText("Session State")).toBeInTheDocument();
    });
  });

  it("renders empty state when no context available", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(null),
    });

    render(
      <SessionContextPanel projectId="my-project" sessionId="happy-pid-12345" />
    );

    await waitFor(() => {
      expect(screen.getByText(/no context available/i)).toBeInTheDocument();
    });
  });

  it("is keyboard navigable", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockContextResponse),
    });

    render(
      <SessionContextPanel projectId="my-project" sessionId="happy-pid-12345" />
    );

    await waitFor(() => {
      expect(screen.getByText("Session State")).toBeInTheDocument();
    });

    const jsonToggle = screen.getByRole("button", { name: /json/i });
    jsonToggle.focus();
    expect(document.activeElement).toBe(jsonToggle);

    // Native button elements respond to click, not keyDown
    // Test that the element is focusable and clickable
    fireEvent.click(jsonToggle);

    await waitFor(() => {
      expect(screen.getByRole("code")).toBeInTheDocument();
    });
  });

  it("has accessible aria labels", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockContextResponse),
    });

    render(
      <SessionContextPanel projectId="my-project" sessionId="happy-pid-12345" />
    );

    await waitFor(() => {
      expect(screen.getByRole("region", { name: /session context/i })).toBeInTheDocument();
    });
  });
});
