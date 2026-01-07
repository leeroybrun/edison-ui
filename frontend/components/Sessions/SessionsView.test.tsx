import { render, screen, fireEvent, within } from "@testing-library/react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { SessionsView } from "./SessionsView";
import type { Session } from "./types";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: vi.fn(),
  useSearchParams: vi.fn(),
  usePathname: vi.fn(),
}));

const mockSessions: Session[] = [
  {
    sessionId: "session-1",
    state: "active",
    phase: "implementation",
    owner: "alice",
    taskCount: 5,
    createdAt: "2025-12-27T10:00:00Z",
    lastActiveAt: "2025-12-28T15:30:00Z",
    git: { branchName: "feature/auth", baseBranch: "main" },
  },
  {
    sessionId: "session-2",
    state: "completed",
    phase: "review",
    owner: "bob",
    taskCount: 3,
    createdAt: "2025-12-26T10:00:00Z",
    lastActiveAt: "2025-12-27T12:00:00Z",
    git: { branchName: "feature/api", baseBranch: "main" },
  },
  {
    sessionId: "session-3",
    state: "paused",
    phase: "waiting",
    owner: null,
    taskCount: 8,
    createdAt: "2025-12-25T10:00:00Z",
    lastActiveAt: "2025-12-26T10:00:00Z",
    git: { branchName: "feature/db", baseBranch: "main" },
  },
];

describe("SessionsView", () => {
  const mockPush = vi.fn();
  const mockSearchParams = new URLSearchParams();

  beforeEach(() => {
    vi.clearAllMocks();
    (useRouter as ReturnType<typeof vi.fn>).mockReturnValue({ push: mockPush });
    (useSearchParams as ReturnType<typeof vi.fn>).mockReturnValue(
      mockSearchParams,
    );
    (usePathname as ReturnType<typeof vi.fn>).mockReturnValue(
      "/projects/my-project/sessions",
    );
  });

  describe("View Toggle", () => {
    it("renders list and board view toggle buttons", () => {
      render(<SessionsView projectId="my-project" sessions={mockSessions} />);

      expect(
        screen.getByRole("button", { name: /list view/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /board view/i }),
      ).toBeInTheDocument();
    });

    it("defaults to list view", () => {
      render(<SessionsView projectId="my-project" sessions={mockSessions} />);

      const listButton = screen.getByRole("button", { name: /list view/i });
      expect(listButton).toHaveAttribute("aria-pressed", "true");
    });

    it("switches to board view when board button is clicked", () => {
      render(<SessionsView projectId="my-project" sessions={mockSessions} />);

      const boardButton = screen.getByRole("button", { name: /board view/i });
      fireEvent.click(boardButton);

      expect(mockPush).toHaveBeenCalledWith(
        expect.stringContaining("view=board"),
      );
    });

    it("uses initial view from props", () => {
      render(
        <SessionsView
          initialView="board"
          projectId="my-project"
          sessions={mockSessions}
        />,
      );

      const boardButton = screen.getByRole("button", { name: /board view/i });
      expect(boardButton).toHaveAttribute("aria-pressed", "true");
    });
  });

  describe("List View", () => {
    it("renders sessions in a table format", () => {
      render(<SessionsView projectId="my-project" sessions={mockSessions} />);

      expect(screen.getByRole("table")).toBeInTheDocument();
    });

    it("displays all session IDs in the table", () => {
      render(<SessionsView projectId="my-project" sessions={mockSessions} />);

      expect(screen.getByText("session-1")).toBeInTheDocument();
      expect(screen.getByText("session-2")).toBeInTheDocument();
      expect(screen.getByText("session-3")).toBeInTheDocument();
    });

    it("displays table headers for Session ID, State, Phase, Tasks, Last Active", () => {
      render(<SessionsView projectId="my-project" sessions={mockSessions} />);

      expect(
        screen.getByRole("columnheader", { name: /session id/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("columnheader", { name: /state/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("columnheader", { name: /phase/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("columnheader", { name: /tasks/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("columnheader", { name: /last active/i }),
      ).toBeInTheDocument();
    });

    it("navigates to tasks filtered by session when row is clicked", () => {
      render(<SessionsView projectId="my-project" sessions={mockSessions} />);

      const row = screen.getByText("session-1").closest("tr");
      fireEvent.click(row!);

      // Per spec: selecting a session shows that session's tasks
      expect(mockPush).toHaveBeenCalledWith(
        "/projects/my-project/tasks?sessionId=session-1",
      );
    });

    it("supports keyboard navigation on rows", () => {
      render(<SessionsView projectId="my-project" sessions={mockSessions} />);

      const row = screen.getByText("session-1").closest("tr");
      fireEvent.keyDown(row!, { key: "Enter" });

      // Per spec: selecting a session shows that session's tasks
      expect(mockPush).toHaveBeenCalledWith(
        "/projects/my-project/tasks?sessionId=session-1",
      );
    });
  });

  describe("Board View", () => {
    it("renders columns for all session states", () => {
      render(
        <SessionsView
          initialView="board"
          projectId="my-project"
          sessions={mockSessions}
        />,
      );

      // Check for column headings (h2 elements inside board columns)
      expect(screen.getByTestId("column-draft")).toBeInTheDocument();
      expect(screen.getByTestId("column-active")).toBeInTheDocument();
      expect(screen.getByTestId("column-blocked")).toBeInTheDocument();
      expect(screen.getByTestId("column-paused")).toBeInTheDocument();
      expect(screen.getByTestId("column-done")).toBeInTheDocument();
      expect(screen.getByTestId("column-closing")).toBeInTheDocument();
      expect(screen.getByTestId("column-completed")).toBeInTheDocument();
      expect(screen.getByTestId("column-validated")).toBeInTheDocument();
      expect(screen.getByTestId("column-archived")).toBeInTheDocument();
      expect(screen.getByTestId("column-abandoned")).toBeInTheDocument();
    });

    it("places sessions in correct columns based on state", () => {
      render(
        <SessionsView
          initialView="board"
          projectId="my-project"
          sessions={mockSessions}
        />,
      );

      // Find the Active column and verify session-1 is there
      const activeColumn = screen.getByTestId("column-active");
      expect(within(activeColumn).getByText("session-1")).toBeInTheDocument();

      // Find the Completed column and verify session-2 is there
      const completedColumn = screen.getByTestId("column-completed");
      expect(
        within(completedColumn).getByText("session-2"),
      ).toBeInTheDocument();

      // Find the Paused column and verify session-3 is there
      const pausedColumn = screen.getByTestId("column-paused");
      expect(within(pausedColumn).getByText("session-3")).toBeInTheDocument();
    });

    it("displays session cards with task count in board view", () => {
      render(
        <SessionsView
          initialView="board"
          projectId="my-project"
          sessions={mockSessions}
        />,
      );

      expect(screen.getByText("5 tasks")).toBeInTheDocument();
      expect(screen.getByText("3 tasks")).toBeInTheDocument();
      expect(screen.getByText("8 tasks")).toBeInTheDocument();
    });
  });

  describe("State Filter", () => {
    it("renders state filter buttons", () => {
      render(<SessionsView projectId="my-project" sessions={mockSessions} />);

      expect(
        screen.getByRole("button", { name: /all states/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /^draft$/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /^active$/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /^paused$/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /^completed$/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /^abandoned$/i }),
      ).toBeInTheDocument();
    });

    it("filters sessions by state when filter is clicked", () => {
      render(<SessionsView projectId="my-project" sessions={mockSessions} />);

      const activeFilter = screen.getByRole("button", { name: /^active$/i });
      fireEvent.click(activeFilter);

      expect(mockPush).toHaveBeenCalledWith(
        expect.stringContaining("state=active"),
      );
    });

    it("uses initial state filter from props", () => {
      render(
        <SessionsView
          initialStateFilter="completed"
          projectId="my-project"
          sessions={mockSessions}
        />,
      );

      // Only completed sessions should be visible
      expect(screen.queryByText("session-1")).not.toBeInTheDocument();
      expect(screen.getByText("session-2")).toBeInTheDocument();
      expect(screen.queryByText("session-3")).not.toBeInTheDocument();
    });

    it("clears filter when All States is clicked", () => {
      render(
        <SessionsView
          initialStateFilter="active"
          projectId="my-project"
          sessions={mockSessions}
        />,
      );

      const allFilter = screen.getByRole("button", { name: /all states/i });
      fireEvent.click(allFilter);

      // URL should not contain state param
      expect(mockPush).toHaveBeenCalledWith(
        expect.not.stringContaining("state="),
      );
    });
  });

  describe("Loading State", () => {
    it("displays loading indicator when isLoading is true", () => {
      render(<SessionsView isLoading projectId="my-project" sessions={[]} />);

      expect(screen.getByText(/loading sessions/i)).toBeInTheDocument();
    });
  });

  describe("Error State", () => {
    it("displays error message when error prop is provided", () => {
      render(
        <SessionsView
          error="Failed to fetch sessions"
          projectId="my-project"
          sessions={[]}
        />,
      );

      expect(screen.getByRole("alert")).toBeInTheDocument();
      expect(screen.getByText(/failed to fetch sessions/i)).toBeInTheDocument();
    });
  });

  describe("Empty State", () => {
    it("displays empty state message when no sessions", () => {
      render(<SessionsView projectId="my-project" sessions={[]} />);

      expect(screen.getByText(/no sessions found/i)).toBeInTheDocument();
    });
  });

  describe("Accessibility", () => {
    it("has proper heading structure", () => {
      render(<SessionsView projectId="my-project" sessions={mockSessions} />);

      expect(
        screen.getByRole("heading", { name: /sessions/i }),
      ).toBeInTheDocument();
    });

    it("view toggle buttons have proper aria-pressed state", () => {
      render(<SessionsView projectId="my-project" sessions={mockSessions} />);

      const listButton = screen.getByRole("button", { name: /list view/i });
      const boardButton = screen.getByRole("button", { name: /board view/i });

      expect(listButton).toHaveAttribute("aria-pressed", "true");
      expect(boardButton).toHaveAttribute("aria-pressed", "false");
    });

    it("table rows are focusable", () => {
      render(<SessionsView projectId="my-project" sessions={mockSessions} />);

      const rows = screen.getAllByRole("row");
      // First row is header, data rows should be focusable
      const dataRow = rows[1];
      expect(dataRow).toHaveAttribute("tabindex", "0");
    });
  });
});
