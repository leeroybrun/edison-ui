import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AgentCard } from "./AgentCard";
import type { TrackingRun } from "./types";

const mockActiveRun: TrackingRun = {
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
};

const mockStaleRun: TrackingRun = {
  ...mockActiveRun,
  runId: "run-002",
  isStale: true,
  state: "active",
};

const mockStoppedRun: TrackingRun = {
  ...mockActiveRun,
  runId: "run-003",
  isRunning: false,
  state: "stopped",
};

describe("AgentCard", () => {
  it("renders run ID", () => {
    render(<AgentCard run={mockActiveRun} />);

    expect(screen.getByText("run-001")).toBeInTheDocument();
  });

  it("displays run type badge", () => {
    render(<AgentCard run={mockActiveRun} />);

    expect(screen.getByText("implementation")).toBeInTheDocument();
  });

  it("shows correct type badge colors", () => {
    const types = ["implementation", "validation", "orchestrator"] as const;
    const expectedStyles = {
      implementation: "bg-blue-100",
      validation: "bg-purple-100",
      orchestrator: "bg-orange-100",
    };

    types.forEach((type) => {
      const { container } = render(
        <AgentCard run={{ ...mockActiveRun, type }} />,
      );
      const badge = container.querySelector(`[data-type="${type}"]`);
      expect(badge).toHaveClass(expectedStyles[type]);
    });
  });

  describe("Status indicators", () => {
    it("displays green status for active non-stale run", () => {
      const { container } = render(<AgentCard run={mockActiveRun} />);

      const statusDot = container.querySelector('[data-testid="status-dot"]');
      expect(statusDot).toHaveClass("bg-green-500");
      expect(screen.getByText("Active")).toBeInTheDocument();
    });

    it("displays yellow status for stale run", () => {
      const { container } = render(<AgentCard run={mockStaleRun} />);

      const statusDot = container.querySelector('[data-testid="status-dot"]');
      expect(statusDot).toHaveClass("bg-yellow-500");
      expect(screen.getByText("Stale")).toBeInTheDocument();
    });

    it("displays gray status for stopped run", () => {
      const { container } = render(<AgentCard run={mockStoppedRun} />);

      const statusDot = container.querySelector('[data-testid="status-dot"]');
      expect(statusDot).toHaveClass("bg-gray-400");
      expect(screen.getByText("Stopped")).toBeInTheDocument();
    });
  });

  describe("Task and session info", () => {
    it("displays task ID when present", () => {
      render(<AgentCard run={mockActiveRun} />);

      expect(screen.getByText(/T001/)).toBeInTheDocument();
    });

    it("does not display task ID when null", () => {
      render(<AgentCard run={{ ...mockActiveRun, taskId: null }} />);

      expect(screen.queryByText(/Task:/)).not.toBeInTheDocument();
    });

    it("displays session ID when present", () => {
      render(<AgentCard run={mockActiveRun} />);

      expect(screen.getByText(/session-1/)).toBeInTheDocument();
    });

    it("does not display session ID when null", () => {
      render(<AgentCard run={{ ...mockActiveRun, sessionId: null }} />);

      expect(screen.queryByText(/Session:/)).not.toBeInTheDocument();
    });
  });

  describe("Validator info", () => {
    it("displays validator ID and round when present", () => {
      const validatorRun: TrackingRun = {
        ...mockActiveRun,
        type: "validation",
        validatorId: "validator-1",
        round: 2,
      };
      render(<AgentCard run={validatorRun} />);

      expect(screen.getByText(/validator-1/)).toBeInTheDocument();
      expect(screen.getByText(/Round 2/)).toBeInTheDocument();
    });
  });

  describe("Metadata", () => {
    it("displays model when present", () => {
      render(<AgentCard run={mockActiveRun} />);

      expect(screen.getByText(/claude-3-opus/)).toBeInTheDocument();
    });

    it("displays hostname", () => {
      render(<AgentCard run={mockActiveRun} />);

      expect(screen.getByText(/dev-machine/)).toBeInTheDocument();
    });

    it("displays relative time for last active", () => {
      render(<AgentCard run={mockActiveRun} />);

      // The component should show some form of relative time
      const timeElement = screen.getByTestId("last-active-time");
      expect(timeElement).toBeInTheDocument();
    });
  });

  it("is accessible as an article element", () => {
    render(<AgentCard run={mockActiveRun} />);

    expect(screen.getByRole("article")).toBeInTheDocument();
  });
});
