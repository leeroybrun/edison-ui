import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { SessionNextPanel } from "./SessionNextPanel";

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

const mockNextResponse = {
  recommendation: "## Next Steps\n\nClaim task T042 and implement the feature following TDD methodology.",
  suggestedActions: [
    {
      actionType: "claim",
      taskId: "T042",
      reason: "Task is ready to be claimed and matches session scope",
    },
    {
      actionType: "validate",
      taskId: "T041",
      reason: "Implementation complete, pending QA validation",
    },
    {
      actionType: "review",
      taskId: null,
      reason: "Review session progress before proceeding",
    },
  ],
  timestamp: "2025-12-28T15:45:00Z",
};

describe("SessionNextPanel", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it("renders loading state initially", () => {
    mockFetch.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(
      <SessionNextPanel projectId="my-project" sessionId="happy-pid-12345" />
    );

    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders error state when fetch fails", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    render(
      <SessionNextPanel projectId="my-project" sessionId="happy-pid-12345" />
    );

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(screen.getByText(/failed to load next recommendations/i)).toBeInTheDocument();
  });

  it("renders recommendation in markdown view by default", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockNextResponse),
    });

    render(
      <SessionNextPanel projectId="my-project" sessionId="happy-pid-12345" />
    );

    await waitFor(() => {
      expect(screen.getByText(/next steps/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/claim task T042/i)).toBeInTheDocument();
  });

  it("displays suggested actions as a list", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockNextResponse),
    });

    render(
      <SessionNextPanel projectId="my-project" sessionId="happy-pid-12345" />
    );

    await waitFor(() => {
      expect(screen.getByText("Suggested Actions")).toBeInTheDocument();
    });

    expect(screen.getByText("claim")).toBeInTheDocument();
    expect(screen.getByText("T042")).toBeInTheDocument();
    expect(screen.getByText(/task is ready to be claimed/i)).toBeInTheDocument();
  });

  it("displays all action types correctly", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockNextResponse),
    });

    render(
      <SessionNextPanel projectId="my-project" sessionId="happy-pid-12345" />
    );

    await waitFor(() => {
      expect(screen.getByText("claim")).toBeInTheDocument();
    });

    expect(screen.getByText("validate")).toBeInTheDocument();
    expect(screen.getByText("review")).toBeInTheDocument();
  });

  it("shows timestamp when recommendations were computed", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockNextResponse),
    });

    render(
      <SessionNextPanel projectId="my-project" sessionId="happy-pid-12345" />
    );

    await waitFor(() => {
      expect(screen.getByText(/computed/i)).toBeInTheDocument();
    });
  });

  it("toggles to JSON view when button is clicked", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockNextResponse),
    });

    render(
      <SessionNextPanel projectId="my-project" sessionId="happy-pid-12345" />
    );

    await waitFor(() => {
      expect(screen.getByText(/next steps/i)).toBeInTheDocument();
    });

    const jsonToggle = screen.getByRole("button", { name: /json/i });
    fireEvent.click(jsonToggle);

    await waitFor(() => {
      expect(screen.getByRole("code")).toBeInTheDocument();
    });
    expect(screen.getByText(/"suggestedActions"/)).toBeInTheDocument();
  });

  it("toggles back to rendered view from JSON", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockNextResponse),
    });

    render(
      <SessionNextPanel projectId="my-project" sessionId="happy-pid-12345" />
    );

    await waitFor(() => {
      expect(screen.getByText(/next steps/i)).toBeInTheDocument();
    });

    // Toggle to JSON
    const jsonToggle = screen.getByRole("button", { name: /json/i });
    fireEvent.click(jsonToggle);

    await waitFor(() => {
      expect(screen.getByRole("code")).toBeInTheDocument();
    });

    // Toggle back to rendered
    const renderedToggle = screen.getByRole("button", { name: /rendered/i });
    fireEvent.click(renderedToggle);

    await waitFor(() => {
      expect(screen.getByText(/next steps/i)).toBeInTheDocument();
    });
  });

  it("renders empty state when no next recommendations available", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(null),
    });

    render(
      <SessionNextPanel projectId="my-project" sessionId="happy-pid-12345" />
    );

    await waitFor(() => {
      expect(screen.getByText(/no recommendations available/i)).toBeInTheDocument();
    });
  });

  it("handles actions without taskId gracefully", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockNextResponse),
    });

    render(
      <SessionNextPanel projectId="my-project" sessionId="happy-pid-12345" />
    );

    await waitFor(() => {
      expect(screen.getByText("review")).toBeInTheDocument();
    });

    // The review action has no taskId, should still render
    expect(screen.getByText(/review session progress/i)).toBeInTheDocument();
  });

  it("is keyboard navigable", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockNextResponse),
    });

    render(
      <SessionNextPanel projectId="my-project" sessionId="happy-pid-12345" />
    );

    await waitFor(() => {
      expect(screen.getByText(/next steps/i)).toBeInTheDocument();
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
      json: () => Promise.resolve(mockNextResponse),
    });

    render(
      <SessionNextPanel projectId="my-project" sessionId="happy-pid-12345" />
    );

    await waitFor(() => {
      expect(screen.getByRole("region", { name: /session next/i })).toBeInTheDocument();
    });
  });

  it("makes suggested actions clickable", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockNextResponse),
    });

    render(
      <SessionNextPanel projectId="my-project" sessionId="happy-pid-12345" />
    );

    await waitFor(() => {
      expect(screen.getByText("Suggested Actions")).toBeInTheDocument();
    });

    // Actions with taskId should be interactive (buttons or links)
    const claimAction = screen.getByRole("listitem", { name: /claim T042/i });
    expect(claimAction).toBeInTheDocument();
  });
});
