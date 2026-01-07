import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { AgentsView } from "./AgentsView";
import type { TrackingRun } from "./types";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => "/projects/test-project/agents",
}));

const mockRuns: TrackingRun[] = [
  {
    runId: "run-001",
    type: "implementation",
    taskId: "T001",
    sessionId: "session-1",
    validatorId: null,
    round: null,
    model: "claude-3-opus",
    processId: 12345,
    hostname: "dev-machine",
    startedAt: "2025-01-01T10:00:00Z",
    lastActiveAt: "2025-01-01T10:05:00Z",
    isRunning: true,
    isStale: false,
    state: "active",
  },
  {
    runId: "run-002",
    type: "validation",
    taskId: "T001",
    sessionId: "session-1",
    validatorId: "validator-1",
    round: 1,
    model: "claude-3-sonnet",
    processId: 12346,
    hostname: "dev-machine",
    startedAt: "2025-01-01T10:00:00Z",
    lastActiveAt: "2025-01-01T10:04:00Z",
    isRunning: true,
    isStale: true,
    state: "active",
  },
  {
    runId: "run-003",
    type: "orchestrator",
    taskId: null,
    sessionId: "session-2",
    validatorId: null,
    round: null,
    model: "claude-3-opus",
    processId: 12347,
    hostname: "other-machine",
    startedAt: "2025-01-01T09:00:00Z",
    lastActiveAt: "2025-01-01T09:30:00Z",
    isRunning: false,
    isStale: false,
    state: "stopped",
  },
];

describe("AgentsView", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2025-01-01T10:10:00Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe("Loading state", () => {
    it("displays loading indicator when isLoading is true", () => {
      render(<AgentsView isLoading={true} runs={[]} />);

      expect(screen.getByText("Loading agents...")).toBeInTheDocument();
    });
  });

  describe("Error state", () => {
    it("displays error message when error is provided", () => {
      render(<AgentsView error="Failed to fetch agents" runs={[]} />);

      expect(screen.getByRole("alert")).toBeInTheDocument();
      expect(screen.getByText("Failed to fetch agents")).toBeInTheDocument();
    });
  });

  describe("Empty state", () => {
    it("displays empty message when no runs are provided", () => {
      render(<AgentsView runs={[]} />);

      expect(screen.getByText("No active agents found")).toBeInTheDocument();
    });
  });

  describe("List rendering", () => {
    it("renders list of agent cards", () => {
      render(<AgentsView runs={mockRuns} />);

      expect(screen.getByText("run-001")).toBeInTheDocument();
      expect(screen.getByText("run-002")).toBeInTheDocument();
      expect(screen.getByText("run-003")).toBeInTheDocument();
    });

    it("displays correct count of agents", () => {
      render(<AgentsView runs={mockRuns} />);

      expect(screen.getByText(/3 agents/i)).toBeInTheDocument();
    });
  });

  describe("Filtering", () => {
    it("filters by session ID", () => {
      render(<AgentsView runs={mockRuns} />);

      // Find and click the session filter
      const sessionFilter = screen.getByLabelText(/session/i);
      fireEvent.change(sessionFilter, { target: { value: "session-1" } });

      // Should only show runs from session-1
      expect(screen.getByText("run-001")).toBeInTheDocument();
      expect(screen.getByText("run-002")).toBeInTheDocument();
      expect(screen.queryByText("run-003")).not.toBeInTheDocument();
    });

    it("filters by run type", () => {
      render(<AgentsView runs={mockRuns} />);

      const typeFilter = screen.getByLabelText(/type/i);
      fireEvent.change(typeFilter, { target: { value: "validation" } });

      expect(screen.queryByText("run-001")).not.toBeInTheDocument();
      expect(screen.getByText("run-002")).toBeInTheDocument();
      expect(screen.queryByText("run-003")).not.toBeInTheDocument();
    });

    it("shows no matches message when filters result in empty list", () => {
      render(<AgentsView runs={mockRuns} />);

      // Filter by session-2 (only has orchestrator) and type validation
      // This combination should result in no matches
      const sessionFilter = screen.getByLabelText(/session/i);
      fireEvent.change(sessionFilter, { target: { value: "session-2" } });

      const typeFilter = screen.getByLabelText(/type/i);
      fireEvent.change(typeFilter, { target: { value: "validation" } });

      expect(
        screen.getByText("No agents match your filters"),
      ).toBeInTheDocument();
    });
  });

  describe("Auto-refresh", () => {
    it("renders auto-refresh toggle", () => {
      render(<AgentsView runs={mockRuns} />);

      expect(
        screen.getByRole("checkbox", { name: /auto-refresh/i }),
      ).toBeInTheDocument();
    });

    it("calls onRefresh when auto-refresh is enabled", () => {
      const onRefresh = vi.fn();
      render(
        <AgentsView
          autoRefreshInterval={5000}
          onRefresh={onRefresh}
          runs={mockRuns}
        />,
      );

      const toggle = screen.getByRole("checkbox", { name: /auto-refresh/i });
      fireEvent.click(toggle);

      // Advance timers by the interval
      vi.advanceTimersByTime(5000);

      expect(onRefresh).toHaveBeenCalled();
    });
  });

  describe("Accessibility", () => {
    it("has accessible region for agents list", () => {
      render(<AgentsView runs={mockRuns} />);

      expect(screen.getByRole("region")).toBeInTheDocument();
    });
  });
});
