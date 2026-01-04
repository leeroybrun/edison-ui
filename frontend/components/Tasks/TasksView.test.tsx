import { render, screen, fireEvent, waitFor } from "@testing-library/react";
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
    title: "Setup authentication",
    state: "done",
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
    title: "Create user profile page",
    state: "wip",
    sessionId: "session-1",
    parentId: null,
    dependsOn: ["T001"],
    ready: true,
    blockedBy: [],
    createdAt: "2025-01-02T10:00:00Z",
    updatedAt: "2025-01-03T12:00:00Z",
  },
  {
    taskId: "T003",
    title: "Fix login bug",
    state: "todo",
    sessionId: "session-2",
    parentId: null,
    dependsOn: [],
    ready: true,
    blockedBy: [],
    createdAt: "2025-01-03T10:00:00Z",
    updatedAt: "2025-01-03T10:00:00Z",
  },
  {
    taskId: "T004",
    title: "Subtask for profile",
    state: "todo",
    sessionId: "session-1",
    parentId: "T002",
    dependsOn: [],
    ready: true,
    blockedBy: [],
    createdAt: "2025-01-03T11:00:00Z",
    updatedAt: "2025-01-03T11:00:00Z",
  },
];

const mockSessions: Session[] = [
  { sessionId: "session-1", name: "Feature Sprint" },
  { sessionId: "session-2", name: "Bug Fixes" },
];

describe("TasksView", () => {
  beforeEach(() => {
    mockPush.mockClear();
    // Reset search params
    mockSearchParams.delete("view");
    mockSearchParams.delete("state");
    mockSearchParams.delete("sessionId");
    mockSearchParams.delete("search");
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("View Toggle", () => {
    it("renders view toggle buttons", () => {
      render(
        <TasksView
          tasks={mockTasks}
          sessions={mockSessions}
        />,
      );

      expect(screen.getByRole("button", { name: /list/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /board/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /tree/i })).toBeInTheDocument();
    });

    it("defaults to list view", () => {
      render(
        <TasksView
          tasks={mockTasks}
          sessions={mockSessions}
        />,
      );

      const listButton = screen.getByRole("button", { name: /list/i });
      expect(listButton).toHaveAttribute("aria-pressed", "true");
    });

    it("switches to board view when board button clicked", () => {
      render(
        <TasksView
          tasks={mockTasks}
          sessions={mockSessions}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /board/i }));

      expect(mockPush).toHaveBeenCalled();
    });

    it("switches to tree view when tree button clicked", () => {
      render(
        <TasksView
          tasks={mockTasks}
          sessions={mockSessions}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /tree/i }));

      expect(mockPush).toHaveBeenCalled();
    });
  });

  describe("List View", () => {
    it("displays tasks in a table format", () => {
      render(
        <TasksView
          tasks={mockTasks}
          sessions={mockSessions}
          initialView="list"
        />,
      );

      // Check for table headers
      expect(screen.getByText("ID")).toBeInTheDocument();
      expect(screen.getByText("Title")).toBeInTheDocument();
      expect(screen.getByText("State")).toBeInTheDocument();
      expect(screen.getByText("Session")).toBeInTheDocument();
      expect(screen.getByText("Updated")).toBeInTheDocument();
    });

    it("displays all tasks as rows", () => {
      render(
        <TasksView
          tasks={mockTasks}
          sessions={mockSessions}
          initialView="list"
        />,
      );

      expect(screen.getByText("T001")).toBeInTheDocument();
      expect(screen.getByText("Setup authentication")).toBeInTheDocument();
      expect(screen.getByText("T002")).toBeInTheDocument();
      expect(screen.getByText("Create user profile page")).toBeInTheDocument();
    });

    it("shows sortable column headers", () => {
      render(
        <TasksView
          tasks={mockTasks}
          sessions={mockSessions}
          initialView="list"
        />,
      );

      const idHeader = screen.getByRole("columnheader", { name: /id/i });
      expect(idHeader).toBeInTheDocument();
    });
  });

  describe("Board View", () => {
    it("displays columns for each state", () => {
      render(
        <TasksView
          tasks={mockTasks}
          sessions={mockSessions}
          initialView="board"
        />,
      );

      expect(screen.getByRole("heading", { name: /todo/i })).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: /wip/i })).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: /done/i })).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: /validated/i })).toBeInTheDocument();
    });

    it("places tasks in correct state columns", () => {
      render(
        <TasksView
          tasks={mockTasks}
          sessions={mockSessions}
          initialView="board"
        />,
      );

      // T001 is done, T002 is wip, T003 is todo
      expect(screen.getByText("T001")).toBeInTheDocument();
      expect(screen.getByText("T002")).toBeInTheDocument();
      expect(screen.getByText("T003")).toBeInTheDocument();
    });

    it("displays task cards within columns", () => {
      render(
        <TasksView
          tasks={mockTasks}
          sessions={mockSessions}
          initialView="board"
        />,
      );

      // Cards should show task titles
      expect(screen.getByText("Setup authentication")).toBeInTheDocument();
      expect(screen.getByText("Create user profile page")).toBeInTheDocument();
    });
  });

  describe("Tree View", () => {
    it("displays tasks in hierarchical structure", () => {
      render(
        <TasksView
          tasks={mockTasks}
          sessions={mockSessions}
          initialView="tree"
        />,
      );

      // All top-level tasks should be visible
      expect(screen.getByText("T001")).toBeInTheDocument();
      expect(screen.getByText("T002")).toBeInTheDocument();
      expect(screen.getByText("T003")).toBeInTheDocument();
    });

    it("shows child tasks indented under parents", () => {
      render(
        <TasksView
          tasks={mockTasks}
          sessions={mockSessions}
          initialView="tree"
        />,
      );

      // T004 is a child of T002
      const childTask = screen.getByText("Subtask for profile");
      expect(childTask).toBeInTheDocument();
    });

    it("allows collapsing/expanding tree nodes", () => {
      render(
        <TasksView
          tasks={mockTasks}
          sessions={mockSessions}
          initialView="tree"
        />,
      );

      // Find the expand/collapse button for parent task
      const expandButton = screen.getByRole("button", { name: /toggle.*T002/i });
      expect(expandButton).toBeInTheDocument();
    });
  });

  describe("Filters", () => {
    it("renders filter controls", () => {
      render(
        <TasksView
          tasks={mockTasks}
          sessions={mockSessions}
        />,
      );

      expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/state/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/session/i)).toBeInTheDocument();
    });

    it("filters tasks by search text", async () => {
      render(
        <TasksView
          tasks={mockTasks}
          sessions={mockSessions}
          initialView="list"
        />,
      );

      const searchInput = screen.getByPlaceholderText(/search/i);
      fireEvent.change(searchInput, { target: { value: "profile" } });

      await waitFor(() => {
        expect(screen.getByText("Create user profile page")).toBeInTheDocument();
        expect(screen.queryByText("Setup authentication")).not.toBeInTheDocument();
      });
    });

    it("filters tasks by state", async () => {
      render(
        <TasksView
          tasks={mockTasks}
          sessions={mockSessions}
          initialView="list"
        />,
      );

      const stateSelect = screen.getByLabelText(/state/i);
      fireEvent.change(stateSelect, { target: { value: "wip" } });

      await waitFor(() => {
        expect(screen.getByText("T002")).toBeInTheDocument();
        expect(screen.queryByText("T001")).not.toBeInTheDocument();
      });
    });

    it("filters tasks by session", async () => {
      render(
        <TasksView
          tasks={mockTasks}
          sessions={mockSessions}
          initialView="list"
        />,
      );

      const sessionSelect = screen.getByLabelText(/session/i);
      fireEvent.change(sessionSelect, { target: { value: "session-2" } });

      await waitFor(() => {
        expect(screen.getByText("T003")).toBeInTheDocument();
        expect(screen.queryByText("T001")).not.toBeInTheDocument();
      });
    });

    it("filters for unscoped tasks when sessionId=none is selected", async () => {
      const tasksWithUnscoped: Task[] = [
        ...mockTasks,
        {
          taskId: "T005",
          title: "Unscoped global task",
          state: "todo",
          sessionId: null,
          parentId: null,
          dependsOn: [],
          ready: true,
          blockedBy: [],
          createdAt: "2025-01-04T10:00:00Z",
          updatedAt: "2025-01-04T10:00:00Z",
        },
      ];

      render(
        <TasksView
          tasks={tasksWithUnscoped}
          sessions={mockSessions}
          initialView="list"
        />,
      );

      const sessionSelect = screen.getByLabelText(/session/i);
      fireEvent.change(sessionSelect, { target: { value: "none" } });

      await waitFor(() => {
        // Only the unscoped task should be visible
        expect(screen.getByText("T005")).toBeInTheDocument();
        expect(screen.getByText("Unscoped global task")).toBeInTheDocument();
        // Session-scoped tasks should be hidden
        expect(screen.queryByText("T001")).not.toBeInTheDocument();
        expect(screen.queryByText("T002")).not.toBeInTheDocument();
        expect(screen.queryByText("T003")).not.toBeInTheDocument();
      });
    });

    it("updates URL query params when filters change", () => {
      render(
        <TasksView
          tasks={mockTasks}
          sessions={mockSessions}
        />,
      );

      const stateSelect = screen.getByLabelText(/state/i);
      fireEvent.change(stateSelect, { target: { value: "done" } });

      expect(mockPush).toHaveBeenCalled();
    });
  });

  describe("Empty State", () => {
    it("shows empty state when no tasks", () => {
      render(
        <TasksView
          tasks={[]}
          sessions={[]}
        />,
      );

      expect(screen.getByText(/no tasks/i)).toBeInTheDocument();
    });

    it("shows empty state when filters return no results", async () => {
      render(
        <TasksView
          tasks={mockTasks}
          sessions={mockSessions}
          initialView="list"
        />,
      );

      const searchInput = screen.getByPlaceholderText(/search/i);
      fireEvent.change(searchInput, { target: { value: "nonexistent" } });

      await waitFor(() => {
        expect(screen.getByText(/no tasks match/i)).toBeInTheDocument();
      });
    });
  });

  describe("Accessibility", () => {
    it("has accessible region for tasks list", () => {
      render(
        <TasksView
          tasks={mockTasks}
          sessions={mockSessions}
        />,
      );

      expect(screen.getByRole("region", { name: /tasks/i })).toBeInTheDocument();
    });

    it("view toggle buttons have proper aria-pressed state", () => {
      render(
        <TasksView
          tasks={mockTasks}
          sessions={mockSessions}
          initialView="board"
        />,
      );

      const boardButton = screen.getByRole("button", { name: /board/i });
      expect(boardButton).toHaveAttribute("aria-pressed", "true");

      const listButton = screen.getByRole("button", { name: /list/i });
      expect(listButton).toHaveAttribute("aria-pressed", "false");
    });
  });

  describe("Locked Session Mode", () => {
    it("hides session filter dropdown when lockedSessionId is provided", () => {
      render(
        <TasksView
          lockedSessionId="session-1"
          sessions={mockSessions}
          tasks={mockTasks}
        />,
      );

      // Session filter should not be rendered
      expect(
        screen.queryByLabelText(/session/i)
      ).not.toBeInTheDocument();
    });

    it("displays locked session indicator when lockedSessionId is provided", () => {
      render(
        <TasksView
          lockedSessionId="session-1"
          sessions={mockSessions}
          tasks={mockTasks}
        />,
      );

      // Should show a badge/indicator for the locked session
      const indicator = screen.getByTestId("locked-session-indicator");
      expect(indicator).toBeInTheDocument();
      expect(indicator).toHaveTextContent(/session: session-1/i);
    });

    it("filters tasks to only show those matching lockedSessionId", async () => {
      render(
        <TasksView
          lockedSessionId="session-1"
          sessions={mockSessions}
          tasks={mockTasks}
        />,
      );

      // Tasks from session-1 should be visible
      expect(screen.getByText("T001")).toBeInTheDocument();
      expect(screen.getByText("T002")).toBeInTheDocument();
      // Tasks from session-2 should NOT be visible
      expect(screen.queryByText("T003")).not.toBeInTheDocument();
    });

    it("still allows state filtering when in locked session mode", async () => {
      render(
        <TasksView
          lockedSessionId="session-1"
          sessions={mockSessions}
          tasks={mockTasks}
        />,
      );

      const stateFilter = screen.getByLabelText(/state/i);
      fireEvent.change(stateFilter, { target: { value: "done" } });

      await waitFor(() => {
        // Only done tasks from session-1 should be visible
        expect(screen.getByText("T001")).toBeInTheDocument();
        expect(screen.queryByText("T002")).not.toBeInTheDocument();
      });
    });

    it("still allows search when in locked session mode", async () => {
      render(
        <TasksView
          lockedSessionId="session-1"
          sessions={mockSessions}
          tasks={mockTasks}
        />,
      );

      const searchInput = screen.getByPlaceholderText(/search/i);
      fireEvent.change(searchInput, { target: { value: "authentication" } });

      await waitFor(() => {
        expect(screen.getByText("T001")).toBeInTheDocument();
        expect(screen.queryByText("T002")).not.toBeInTheDocument();
      });
    });

    it("shows no tasks message when locked session has no tasks", () => {
      render(
        <TasksView
          lockedSessionId="non-existent-session"
          sessions={mockSessions}
          tasks={mockTasks}
        />,
      );

      expect(screen.getByText(/no tasks match/i)).toBeInTheDocument();
    });

    it("does not update URL with sessionId when lockedSessionId is used", async () => {
      render(
        <TasksView
          lockedSessionId="session-1"
          sessions={mockSessions}
          tasks={mockTasks}
        />,
      );

      // The URL should not contain sessionId param since it's locked
      const stateFilter = screen.getByLabelText(/state/i);
      fireEvent.change(stateFilter, { target: { value: "done" } });

      await waitFor(() => {
        // When state filter is applied, sessionId should NOT appear in URL
        const pushedUrl = mockPush.mock.calls[0]?.[0] || "";
        expect(pushedUrl).not.toContain("sessionId=");
      });
    });
  });
});
