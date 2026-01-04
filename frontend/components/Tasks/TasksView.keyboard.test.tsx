import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { TasksView } from "./TasksView";
import type { Task, Session } from "./types";

// Mock next/navigation
const mockPush = vi.fn();
const mockSearchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockPush,
  }),
  useSearchParams: () => mockSearchParams,
  usePathname: () => "/projects/test-project/tasks",
}));

const mockTasks: Task[] = [
  {
    taskId: "T001",
    title: "First task",
    state: "todo",
    sessionId: "session-1",
    parentId: null,
    dependsOn: [],
    ready: true,
    blockedBy: [],
    createdAt: "2025-01-01T10:00:00Z",
    updatedAt: "2025-01-02T15:30:00Z",
  },
  {
    taskId: "T002",
    title: "Second task",
    state: "wip",
    sessionId: "session-1",
    parentId: null,
    dependsOn: [],
    ready: true,
    blockedBy: [],
    createdAt: "2025-01-02T10:00:00Z",
    updatedAt: "2025-01-03T12:00:00Z",
  },
  {
    taskId: "T003",
    title: "Third task",
    state: "done",
    sessionId: "session-1",
    parentId: null,
    dependsOn: [],
    ready: true,
    blockedBy: [],
    createdAt: "2025-01-03T10:00:00Z",
    updatedAt: "2025-01-03T10:00:00Z",
  },
  {
    taskId: "T004",
    title: "Fourth task",
    state: "validated",
    sessionId: "session-1",
    parentId: null,
    dependsOn: [],
    ready: true,
    blockedBy: [],
    createdAt: "2025-01-03T11:00:00Z",
    updatedAt: "2025-01-03T11:00:00Z",
  },
];

const mockSessions: Session[] = [
  { sessionId: "session-1", name: "Feature Sprint" },
];

describe("TasksView Keyboard Navigation", () => {
  beforeEach(() => {
    mockPush.mockClear();
    mockSearchParams.delete("view");
    mockSearchParams.delete("state");
    mockSearchParams.delete("sessionId");
    mockSearchParams.delete("search");
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("List View Navigation", () => {
    it("moves selection down with ArrowDown", async () => {
      const user = userEvent.setup();
      render(
        <TasksView
          initialView="list"
          sessions={mockSessions}
          tasks={mockTasks}
        />,
      );

      // Focus the tasks region
      const region = screen.getByRole("region", { name: /tasks/i });
      await user.click(region);

      await user.keyboard("{ArrowDown}");

      const rows = screen.getAllByRole("row").slice(1); // Skip header row
      expect(rows[0]).toHaveAttribute("data-selected", "true");
    });

    it("moves selection up with ArrowUp", async () => {
      const user = userEvent.setup();
      render(
        <TasksView
          initialView="list"
          sessions={mockSessions}
          tasks={mockTasks}
        />,
      );

      const region = screen.getByRole("region", { name: /tasks/i });
      await user.click(region);

      await user.keyboard("{ArrowDown}{ArrowDown}{ArrowUp}");

      const rows = screen.getAllByRole("row").slice(1);
      expect(rows[0]).toHaveAttribute("data-selected", "true");
    });

    it("moves selection down with j (vim-style)", async () => {
      const user = userEvent.setup();
      render(
        <TasksView
          initialView="list"
          sessions={mockSessions}
          tasks={mockTasks}
        />,
      );

      const region = screen.getByRole("region", { name: /tasks/i });
      await user.click(region);

      await user.keyboard("j");

      const rows = screen.getAllByRole("row").slice(1);
      expect(rows[0]).toHaveAttribute("data-selected", "true");
    });

    it("moves selection up with k (vim-style)", async () => {
      const user = userEvent.setup();
      render(
        <TasksView
          initialView="list"
          sessions={mockSessions}
          tasks={mockTasks}
        />,
      );

      const region = screen.getByRole("region", { name: /tasks/i });
      await user.click(region);

      await user.keyboard("jjk");

      const rows = screen.getAllByRole("row").slice(1);
      expect(rows[0]).toHaveAttribute("data-selected", "true");
    });

    it("opens task on Enter", async () => {
      const user = userEvent.setup();
      const onTaskSelect = vi.fn();
      render(
        <TasksView
          initialView="list"
          onTaskSelect={onTaskSelect}
          sessions={mockSessions}
          tasks={mockTasks}
        />,
      );

      const region = screen.getByRole("region", { name: /tasks/i });
      await user.click(region);

      await user.keyboard("{ArrowDown}{Enter}");

      expect(onTaskSelect).toHaveBeenCalledWith("T001");
    });

    it("wraps selection at the end of list", async () => {
      const user = userEvent.setup();
      render(
        <TasksView
          initialView="list"
          sessions={mockSessions}
          tasks={mockTasks}
        />,
      );

      const region = screen.getByRole("region", { name: /tasks/i });
      await user.click(region);

      // Move past the end
      await user.keyboard("{ArrowDown}{ArrowDown}{ArrowDown}{ArrowDown}{ArrowDown}");

      const rows = screen.getAllByRole("row").slice(1);
      expect(rows[0]).toHaveAttribute("data-selected", "true");
    });

    it("clears selection on Escape", async () => {
      const user = userEvent.setup();
      render(
        <TasksView
          initialView="list"
          sessions={mockSessions}
          tasks={mockTasks}
        />,
      );

      const region = screen.getByRole("region", { name: /tasks/i });
      await user.click(region);

      await user.keyboard("{ArrowDown}{Escape}");

      const rows = screen.getAllByRole("row").slice(1);
      rows.forEach((row) => {
        expect(row).not.toHaveAttribute("data-selected", "true");
      });
    });
  });

  describe("Board View Navigation", () => {
    it("moves selection right between columns with Tab", async () => {
      const user = userEvent.setup();
      render(
        <TasksView
          initialView="board"
          sessions={mockSessions}
          tasks={mockTasks}
        />,
      );

      const region = screen.getByRole("region", { name: /tasks/i });
      await user.click(region);

      // First ArrowDown selects first task in first column
      await user.keyboard("{ArrowDown}");
      // Tab moves to next column
      await user.keyboard("{Tab}");

      // Should now have selection in the next column
      const wipHeading = screen.getByRole("heading", { name: /wip/i });
      const wipColumn = wipHeading.closest('[data-column]');
      const wipCards = wipColumn?.querySelectorAll('[data-selected="true"]');
      expect(wipCards?.length).toBeGreaterThan(0);
    });

    it("moves selection left between columns with Shift+Tab", async () => {
      const user = userEvent.setup();
      render(
        <TasksView
          initialView="board"
          sessions={mockSessions}
          tasks={mockTasks}
        />,
      );

      const region = screen.getByRole("region", { name: /tasks/i });
      await user.click(region);

      // Navigate to second column first
      await user.keyboard("{ArrowDown}{Tab}");
      // Then go back
      await user.keyboard("{Shift>}{Tab}{/Shift}");

      // Should be back in first column
      const todoHeading = screen.getByRole("heading", { name: /todo/i });
      const todoColumn = todoHeading.closest('[data-column]');
      const todoCards = todoColumn?.querySelectorAll('[data-selected="true"]');
      expect(todoCards?.length).toBeGreaterThan(0);
    });

    it("navigates within column with ArrowDown/ArrowUp", async () => {
      const user = userEvent.setup();
      const tasksWithMultipleInColumn: Task[] = [
        { ...mockTasks[0], state: "todo" },
        { ...mockTasks[1], taskId: "T005", state: "todo" },
      ];
      render(
        <TasksView
          initialView="board"
          sessions={mockSessions}
          tasks={tasksWithMultipleInColumn}
        />,
      );

      const region = screen.getByRole("region", { name: /tasks/i });
      await user.click(region);

      await user.keyboard("{ArrowDown}"); // Select first
      await user.keyboard("{ArrowDown}"); // Select second

      const cards = screen.getAllByRole("article");
      expect(cards[1]).toHaveAttribute("data-selected", "true");
    });

    it("opens task on Enter in board view", async () => {
      const user = userEvent.setup();
      const onTaskSelect = vi.fn();
      render(
        <TasksView
          initialView="board"
          onTaskSelect={onTaskSelect}
          sessions={mockSessions}
          tasks={mockTasks}
        />,
      );

      const region = screen.getByRole("region", { name: /tasks/i });
      await user.click(region);

      await user.keyboard("{ArrowDown}{Enter}");

      expect(onTaskSelect).toHaveBeenCalled();
    });
  });

  describe("Tree View Navigation", () => {
    it("expands collapsed node with ArrowRight", async () => {
      const user = userEvent.setup();
      const tasksWithChildren: Task[] = [
        ...mockTasks,
        {
          taskId: "T005",
          title: "Child task",
          state: "todo",
          sessionId: "session-1",
          parentId: "T001",
          dependsOn: [],
          ready: true,
          blockedBy: [],
          createdAt: "2025-01-03T11:00:00Z",
          updatedAt: "2025-01-03T11:00:00Z",
        },
      ];

      render(
        <TasksView
          initialView="tree"
          sessions={mockSessions}
          tasks={tasksWithChildren}
        />,
      );

      const region = screen.getByRole("region", { name: /tasks/i });
      await user.click(region);

      await user.keyboard("{ArrowDown}"); // Select T001
      await user.keyboard("{ArrowRight}"); // Expand

      // Child should be visible
      expect(screen.getByText("Child task")).toBeInTheDocument();
    });

    it("collapses expanded node with ArrowLeft", async () => {
      const user = userEvent.setup();
      const tasksWithChildren: Task[] = [
        ...mockTasks,
        {
          taskId: "T005",
          title: "Child task",
          state: "todo",
          sessionId: "session-1",
          parentId: "T001",
          dependsOn: [],
          ready: true,
          blockedBy: [],
          createdAt: "2025-01-03T11:00:00Z",
          updatedAt: "2025-01-03T11:00:00Z",
        },
      ];

      render(
        <TasksView
          initialView="tree"
          sessions={mockSessions}
          tasks={tasksWithChildren}
        />,
      );

      const region = screen.getByRole("region", { name: /tasks/i });
      await user.click(region);

      await user.keyboard("{ArrowDown}"); // Select T001
      await user.keyboard("{ArrowLeft}"); // Collapse

      // Toggle button should be in collapsed state
      const toggleButton = screen.getByRole("button", { name: /toggle.*T001/i });
      expect(toggleButton.querySelector("svg")).not.toHaveClass("rotate-90");
    });

    it("moves to parent with ArrowLeft on leaf node", async () => {
      const user = userEvent.setup();
      const tasksWithChildren: Task[] = [
        {
          taskId: "T001",
          title: "Parent task",
          state: "todo",
          sessionId: "session-1",
          parentId: null,
          dependsOn: [],
          ready: true,
          blockedBy: [],
          createdAt: "2025-01-01T10:00:00Z",
          updatedAt: "2025-01-02T15:30:00Z",
        },
        {
          taskId: "T005",
          title: "Child task",
          state: "todo",
          sessionId: "session-1",
          parentId: "T001",
          dependsOn: [],
          ready: true,
          blockedBy: [],
          createdAt: "2025-01-03T11:00:00Z",
          updatedAt: "2025-01-03T11:00:00Z",
        },
      ];

      render(
        <TasksView
          initialView="tree"
          sessions={mockSessions}
          tasks={tasksWithChildren}
        />,
      );

      const region = screen.getByRole("region", { name: /tasks/i });
      await user.click(region);

      // Navigate to child (T005 is at index 1 in filteredTasks)
      await user.keyboard("{ArrowDown}"); // Select T001 (index 0)
      await user.keyboard("{ArrowDown}"); // Select T005 (index 1)

      // Now press ArrowLeft to go back to parent
      await user.keyboard("{ArrowLeft}"); // Back to T001

      // Parent should be selected (index 0)
      const parentContainer = screen.getByText("T001").closest("[data-selected]");
      expect(parentContainer).not.toBeNull();
    });
  });

  describe("Accessibility", () => {
    it("has proper aria-activedescendant when navigating", async () => {
      const user = userEvent.setup();
      render(
        <TasksView
          initialView="list"
          sessions={mockSessions}
          tasks={mockTasks}
        />,
      );

      const region = screen.getByRole("region", { name: /tasks/i });
      await user.click(region);

      await user.keyboard("{ArrowDown}");

      const table = screen.getByRole("table");
      const rows = screen.getAllByRole("row").slice(1);
      expect(table).toHaveAttribute("aria-activedescendant", rows[0].id);
    });

    it("announces selection changes to screen readers", async () => {
      const user = userEvent.setup();
      render(
        <TasksView
          initialView="list"
          sessions={mockSessions}
          tasks={mockTasks}
        />,
      );

      const region = screen.getByRole("region", { name: /tasks/i });
      await user.click(region);

      await user.keyboard("{ArrowDown}");

      // Check for aria-live region or aria-selected
      const rows = screen.getAllByRole("row").slice(1);
      expect(rows[0]).toHaveAttribute("aria-selected", "true");
    });
  });
});
