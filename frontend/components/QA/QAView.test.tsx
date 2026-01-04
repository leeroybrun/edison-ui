import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { QAView } from "./QAView";
import type { QARecord, Session } from "./types";

// Mock next/navigation
const mockPush = vi.fn();
const mockSearchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockPush,
  }),
  useSearchParams: () => mockSearchParams,
  usePathname: () => "/projects/test-project/qa",
}));

const mockQARecords: QARecord[] = [
  {
    qaId: "QA001",
    taskId: "T001",
    sessionId: "session-1",
    round: 1,
    state: "done",
    verdict: "passed",
    validators: ["validator-1"],
    createdAt: "2025-01-01T10:00:00Z",
    updatedAt: "2025-01-02T15:30:00Z",
  },
  {
    qaId: "QA002",
    taskId: "T002",
    sessionId: "session-1",
    round: 1,
    state: "wip",
    verdict: "in_progress",
    validators: ["validator-2"],
    createdAt: "2025-01-02T10:00:00Z",
    updatedAt: "2025-01-03T12:00:00Z",
  },
  {
    qaId: "QA003",
    taskId: "T003",
    sessionId: "session-2",
    round: 2,
    state: "todo",
    verdict: null,
    validators: [],
    createdAt: "2025-01-03T10:00:00Z",
    updatedAt: "2025-01-03T10:00:00Z",
  },
  {
    qaId: "QA004",
    taskId: "T004",
    sessionId: "session-1",
    round: 1,
    state: "done",
    verdict: "rejected",
    validators: ["validator-1", "validator-3"],
    createdAt: "2025-01-03T11:00:00Z",
    updatedAt: "2025-01-03T11:00:00Z",
  },
  {
    qaId: "QA005",
    taskId: "T005",
    sessionId: null,
    round: 1,
    state: "waiting",
    verdict: null,
    validators: [],
    createdAt: "2025-01-04T10:00:00Z",
    updatedAt: "2025-01-04T10:00:00Z",
  },
];

const mockSessions: Session[] = [
  { sessionId: "session-1", name: "Feature Sprint" },
  { sessionId: "session-2", name: "Bug Fixes" },
];

describe("QAView", () => {
  beforeEach(() => {
    mockPush.mockClear();
    // Reset search params
    mockSearchParams.delete("view");
    mockSearchParams.delete("state");
    mockSearchParams.delete("verdict");
    mockSearchParams.delete("sessionId");
    mockSearchParams.delete("validator");
    mockSearchParams.delete("search");
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("View Toggle", () => {
    it("renders view toggle buttons", () => {
      render(<QAView qaRecords={mockQARecords} sessions={mockSessions} />);

      expect(screen.getByRole("button", { name: /list/i })).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /board/i })
      ).toBeInTheDocument();
    });

    it("defaults to list view", () => {
      render(<QAView qaRecords={mockQARecords} sessions={mockSessions} />);

      const listButton = screen.getByRole("button", { name: /list/i });
      expect(listButton).toHaveAttribute("aria-pressed", "true");
    });

    it("switches to board view when board button clicked", () => {
      render(<QAView qaRecords={mockQARecords} sessions={mockSessions} />);

      fireEvent.click(screen.getByRole("button", { name: /board/i }));

      expect(mockPush).toHaveBeenCalled();
    });
  });

  describe("List View", () => {
    it("displays QA records in a table format", () => {
      render(
        <QAView
          initialView="list"
          qaRecords={mockQARecords}
          sessions={mockSessions}
        />
      );

      // Check for table headers
      expect(screen.getByText("QA ID")).toBeInTheDocument();
      expect(screen.getByText("Task")).toBeInTheDocument();
      expect(screen.getByText("State")).toBeInTheDocument();
      expect(screen.getByText("Verdict")).toBeInTheDocument();
      expect(screen.getByText("Round")).toBeInTheDocument();
      expect(screen.getByText("Validators")).toBeInTheDocument();
    });

    it("displays all QA records as rows", () => {
      render(
        <QAView
          initialView="list"
          qaRecords={mockQARecords}
          sessions={mockSessions}
        />
      );

      expect(screen.getByText("QA001")).toBeInTheDocument();
      expect(screen.getByText("QA002")).toBeInTheDocument();
      expect(screen.getByText("QA003")).toBeInTheDocument();
      expect(screen.getByText("QA004")).toBeInTheDocument();
    });

    it("shows task ID for each QA record", () => {
      render(
        <QAView
          initialView="list"
          qaRecords={mockQARecords}
          sessions={mockSessions}
        />
      );

      expect(screen.getByText("T001")).toBeInTheDocument();
      expect(screen.getByText("T002")).toBeInTheDocument();
    });

    it("displays verdict badges with correct colors", () => {
      render(
        <QAView
          initialView="list"
          qaRecords={mockQARecords}
          sessions={mockSessions}
        />
      );

      // Check verdict displays
      expect(screen.getByText("passed")).toBeInTheDocument();
      expect(screen.getByText("rejected")).toBeInTheDocument();
      expect(screen.getByText("in_progress")).toBeInTheDocument();
    });
  });

  describe("Board View", () => {
    it("displays columns for each state", () => {
      render(
        <QAView
          initialView="board"
          qaRecords={mockQARecords}
          sessions={mockSessions}
        />
      );

      expect(
        screen.getByRole("heading", { name: /waiting/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("heading", { name: /todo/i })
      ).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: /wip/i })).toBeInTheDocument();
      expect(
        screen.getByRole("heading", { name: /done/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("heading", { name: /validated/i })
      ).toBeInTheDocument();
    });

    it("places QA records in correct state columns", () => {
      render(
        <QAView
          initialView="board"
          qaRecords={mockQARecords}
          sessions={mockSessions}
        />
      );

      // QA001 is done, QA002 is wip, QA003 is todo
      expect(screen.getByText("QA001")).toBeInTheDocument();
      expect(screen.getByText("QA002")).toBeInTheDocument();
      expect(screen.getByText("QA003")).toBeInTheDocument();
    });

    it("displays QA cards within columns", () => {
      render(
        <QAView
          initialView="board"
          qaRecords={mockQARecords}
          sessions={mockSessions}
        />
      );

      // Cards should show task IDs
      expect(screen.getByText("T001")).toBeInTheDocument();
      expect(screen.getByText("T002")).toBeInTheDocument();
    });
  });

  describe("Filters", () => {
    it("renders filter controls", () => {
      render(<QAView qaRecords={mockQARecords} sessions={mockSessions} />);

      expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/state/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/verdict/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/session/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/validator/i)).toBeInTheDocument();
    });

    it("filters QA records by search text", async () => {
      render(
        <QAView
          initialView="list"
          qaRecords={mockQARecords}
          sessions={mockSessions}
        />
      );

      const searchInput = screen.getByPlaceholderText(/search/i);
      fireEvent.change(searchInput, { target: { value: "QA001" } });

      await waitFor(() => {
        expect(screen.getByText("QA001")).toBeInTheDocument();
        expect(screen.queryByText("QA002")).not.toBeInTheDocument();
      });
    });

    it("filters QA records by state", async () => {
      render(
        <QAView
          initialView="list"
          qaRecords={mockQARecords}
          sessions={mockSessions}
        />
      );

      const stateSelect = screen.getByLabelText(/state/i);
      fireEvent.change(stateSelect, { target: { value: "wip" } });

      await waitFor(() => {
        expect(screen.getByText("QA002")).toBeInTheDocument();
        expect(screen.queryByText("QA001")).not.toBeInTheDocument();
      });
    });

    it("filters QA records by verdict", async () => {
      render(
        <QAView
          initialView="list"
          qaRecords={mockQARecords}
          sessions={mockSessions}
        />
      );

      const verdictSelect = screen.getByLabelText(/verdict/i);
      fireEvent.change(verdictSelect, { target: { value: "passed" } });

      await waitFor(() => {
        expect(screen.getByText("QA001")).toBeInTheDocument();
        expect(screen.queryByText("QA004")).not.toBeInTheDocument();
      });
    });

    it("filters QA records by session", async () => {
      render(
        <QAView
          initialView="list"
          qaRecords={mockQARecords}
          sessions={mockSessions}
        />
      );

      const sessionSelect = screen.getByLabelText(/session/i);
      fireEvent.change(sessionSelect, { target: { value: "session-2" } });

      await waitFor(() => {
        expect(screen.getByText("QA003")).toBeInTheDocument();
        expect(screen.queryByText("QA001")).not.toBeInTheDocument();
      });
    });

    it("filters QA records by validator", async () => {
      render(
        <QAView
          initialView="list"
          qaRecords={mockQARecords}
          sessions={mockSessions}
        />
      );

      const validatorInput = screen.getByLabelText(/validator/i);
      fireEvent.change(validatorInput, { target: { value: "validator-1" } });

      await waitFor(() => {
        expect(screen.getByText("QA001")).toBeInTheDocument();
        expect(screen.getByText("QA004")).toBeInTheDocument();
        expect(screen.queryByText("QA002")).not.toBeInTheDocument();
      });
    });

    it("filters for unscoped QA when sessionId=none is selected", async () => {
      render(
        <QAView
          initialView="list"
          qaRecords={mockQARecords}
          sessions={mockSessions}
        />
      );

      const sessionSelect = screen.getByLabelText(/session/i);
      fireEvent.change(sessionSelect, { target: { value: "none" } });

      await waitFor(() => {
        // Only the unscoped QA should be visible
        expect(screen.getByText("QA005")).toBeInTheDocument();
        // Session-scoped QA should be hidden
        expect(screen.queryByText("QA001")).not.toBeInTheDocument();
      });
    });

    it("updates URL query params when filters change", () => {
      render(<QAView qaRecords={mockQARecords} sessions={mockSessions} />);

      const stateSelect = screen.getByLabelText(/state/i);
      fireEvent.change(stateSelect, { target: { value: "done" } });

      expect(mockPush).toHaveBeenCalled();
    });
  });

  describe("Empty State", () => {
    it("shows empty state when no QA records", () => {
      render(<QAView qaRecords={[]} sessions={[]} />);

      expect(screen.getByText(/no qa records/i)).toBeInTheDocument();
    });

    it("shows empty state when filters return no results", async () => {
      render(
        <QAView
          initialView="list"
          qaRecords={mockQARecords}
          sessions={mockSessions}
        />
      );

      const searchInput = screen.getByPlaceholderText(/search/i);
      fireEvent.change(searchInput, { target: { value: "nonexistent" } });

      await waitFor(() => {
        expect(screen.getByText(/no qa records match/i)).toBeInTheDocument();
      });
    });
  });

  describe("Accessibility", () => {
    it("has accessible region for QA list", () => {
      render(<QAView qaRecords={mockQARecords} sessions={mockSessions} />);

      expect(screen.getByRole("region", { name: /qa/i })).toBeInTheDocument();
    });

    it("view toggle buttons have proper aria-pressed state", () => {
      render(
        <QAView
          initialView="board"
          qaRecords={mockQARecords}
          sessions={mockSessions}
        />
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
        <QAView
          lockedSessionId="session-1"
          qaRecords={mockQARecords}
          sessions={mockSessions}
        />
      );

      // Session filter should not be rendered
      expect(screen.queryByLabelText(/session/i)).not.toBeInTheDocument();
    });

    it("displays locked session indicator when lockedSessionId is provided", () => {
      render(
        <QAView
          lockedSessionId="session-1"
          qaRecords={mockQARecords}
          sessions={mockSessions}
        />
      );

      // Should show a badge/indicator for the locked session
      const indicator = screen.getByTestId("locked-session-indicator");
      expect(indicator).toBeInTheDocument();
      expect(indicator).toHaveTextContent(/session: session-1/i);
    });

    it("filters QA records to only show those matching lockedSessionId", async () => {
      render(
        <QAView
          lockedSessionId="session-1"
          qaRecords={mockQARecords}
          sessions={mockSessions}
        />
      );

      // QA from session-1 should be visible
      expect(screen.getByText("QA001")).toBeInTheDocument();
      expect(screen.getByText("QA002")).toBeInTheDocument();
      // QA from session-2 should NOT be visible
      expect(screen.queryByText("QA003")).not.toBeInTheDocument();
    });

    it("still allows state filtering when in locked session mode", async () => {
      render(
        <QAView
          lockedSessionId="session-1"
          qaRecords={mockQARecords}
          sessions={mockSessions}
        />
      );

      const stateFilter = screen.getByLabelText(/state/i);
      fireEvent.change(stateFilter, { target: { value: "done" } });

      await waitFor(() => {
        // Only done QA from session-1 should be visible
        expect(screen.getByText("QA001")).toBeInTheDocument();
        expect(screen.queryByText("QA002")).not.toBeInTheDocument();
      });
    });
  });

  describe("Error State", () => {
    it("displays error message when error prop is provided", () => {
      render(
        <QAView
          error="Failed to load QA records"
          qaRecords={[]}
          sessions={[]}
        />
      );

      expect(screen.getByRole("alert")).toBeInTheDocument();
      expect(screen.getByText("Failed to load QA records")).toBeInTheDocument();
    });
  });

  describe("Loading State", () => {
    it("displays loading message when isLoading is true", () => {
      render(<QAView isLoading qaRecords={[]} sessions={[]} />);

      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });
  });
});
