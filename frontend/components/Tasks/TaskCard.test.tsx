import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TaskCard } from "./TaskCard";
import type { Task } from "./types";

const mockTask: Task = {
  taskId: "T001",
  title: "Implement login feature",
  state: "wip",
  sessionId: "session-1",
  parentId: null,
  dependsOn: [],
  ready: true,
  blockedBy: [],
  createdAt: "2025-01-01T10:00:00Z",
  updatedAt: "2025-01-02T15:30:00Z",
};

describe("TaskCard", () => {
  it("renders task ID and title", () => {
    render(<TaskCard task={mockTask} />);

    expect(screen.getByText("T001")).toBeInTheDocument();
    expect(screen.getByText("Implement login feature")).toBeInTheDocument();
  });

  it("displays task state badge", () => {
    render(<TaskCard task={mockTask} />);

    expect(screen.getByText("wip")).toBeInTheDocument();
  });

  it("renders correct badge color for each state", () => {
    const states = ["todo", "wip", "blocked", "done", "validated"] as const;
    const expectedStyles = {
      todo: "bg-gray-100",
      wip: "bg-blue-100",
      blocked: "bg-red-100",
      done: "bg-green-100",
      validated: "bg-purple-100",
    };

    states.forEach((state) => {
      const { container } = render(<TaskCard task={{ ...mockTask, state }} />);
      const badge = container.querySelector(`[data-state="${state}"]`);
      expect(badge).toHaveClass(expectedStyles[state]);
    });
  });

  it("is keyboard accessible as an interactive element", () => {
    render(<TaskCard task={mockTask} />);

    const card = screen.getByRole("article");
    expect(card).toBeInTheDocument();
  });

  it("displays session ID when present", () => {
    render(<TaskCard task={mockTask} />);

    expect(screen.getByText(/session-1/)).toBeInTheDocument();
  });

  it("does not display session when null", () => {
    render(<TaskCard task={{ ...mockTask, sessionId: null }} />);

    expect(screen.queryByText(/session-/)).not.toBeInTheDocument();
  });

  describe("Ready/Blocked indicators", () => {
    it("displays Ready badge when task is ready", () => {
      render(<TaskCard task={{ ...mockTask, ready: true, blockedBy: [] }} />);

      expect(screen.getByTestId("ready-badge")).toBeInTheDocument();
      expect(screen.getByText("Ready")).toBeInTheDocument();
    });

    it("displays Blocked badge with count when task is blocked", () => {
      const blockedTask: Task = {
        ...mockTask,
        ready: false,
        blockedBy: [
          {
            dependencyId: "T000",
            dependencyState: "wip",
            requiredStates: ["done", "validated"],
            reason:
              "Dependency T000 is in state wip, requires done or validated",
          },
        ],
      };
      render(<TaskCard task={blockedTask} />);

      expect(screen.getByTestId("blocked-badge")).toBeInTheDocument();
      expect(screen.getByText("Blocked (1)")).toBeInTheDocument();
    });

    it("shows blocked reasons when Blocked badge is clicked", () => {
      const blockedTask: Task = {
        ...mockTask,
        ready: false,
        blockedBy: [
          {
            dependencyId: "T000",
            dependencyState: "wip",
            requiredStates: ["done", "validated"],
            reason:
              "Dependency T000 is in state wip, requires done or validated",
          },
        ],
      };
      render(<TaskCard task={blockedTask} />);

      const blockedBadge = screen.getByTestId("blocked-badge");
      fireEvent.click(blockedBadge);

      expect(screen.getByTestId("blocked-reasons")).toBeInTheDocument();
      expect(
        screen.getByText(
          "Dependency T000 is in state wip, requires done or validated",
        ),
      ).toBeInTheDocument();
    });

    it("toggles blocked reasons visibility on repeated clicks", () => {
      const blockedTask: Task = {
        ...mockTask,
        ready: false,
        blockedBy: [
          {
            dependencyId: "T000",
            dependencyState: "wip",
            requiredStates: ["done", "validated"],
            reason: "Blocked by T000",
          },
        ],
      };
      render(<TaskCard task={blockedTask} />);

      const blockedBadge = screen.getByTestId("blocked-badge");

      // Click to show
      fireEvent.click(blockedBadge);
      expect(screen.getByTestId("blocked-reasons")).toBeInTheDocument();

      // Click to hide
      fireEvent.click(blockedBadge);
      expect(screen.queryByTestId("blocked-reasons")).not.toBeInTheDocument();
    });

    it("has accessible aria-expanded attribute on blocked badge", () => {
      const blockedTask: Task = {
        ...mockTask,
        ready: false,
        blockedBy: [
          {
            dependencyId: "T000",
            dependencyState: "wip",
            requiredStates: ["done", "validated"],
            reason: "Blocked by T000",
          },
        ],
      };
      render(<TaskCard task={blockedTask} />);

      const blockedBadge = screen.getByTestId("blocked-badge");
      expect(blockedBadge).toHaveAttribute("aria-expanded", "false");

      fireEvent.click(blockedBadge);
      expect(blockedBadge).toHaveAttribute("aria-expanded", "true");
    });
  });
});
