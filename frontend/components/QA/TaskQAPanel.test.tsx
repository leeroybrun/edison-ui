import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TaskQAPanel } from "./TaskQAPanel";
import type { TaskQADetailResponse, RoundEvidence } from "./types";

const mockRoundEvidence: RoundEvidence[] = [
  {
    roundNumber: 1,
    bundleSummary: "Initial implementation bundle",
    implementationReport: "## Summary\nInitial implementation completed",
    validatorReports: [
      {
        validatorId: "code-review",
        verdict: "fail",
        reason: "Missing error handling in API calls",
        reportPath:
          "[REDACTED]/validation-evidence/T001/round-1/code-review.md",
      },
    ],
    artifacts: [
      {
        name: "coverage-report.txt",
        path: "[REDACTED]/validation-evidence/T001/round-1/coverage-report.txt",
        type: "text/plain",
      },
    ],
  },
  {
    roundNumber: 2,
    bundleSummary: "Fixed error handling",
    implementationReport: "## Summary\nAdded error handling",
    validatorReports: [
      {
        validatorId: "code-review",
        verdict: "pass",
        reason: "All checks passed",
        reportPath:
          "[REDACTED]/validation-evidence/T001/round-2/code-review.md",
      },
      {
        validatorId: "test-coverage",
        verdict: "pass",
        reason: "Coverage at 95%",
        reportPath:
          "[REDACTED]/validation-evidence/T001/round-2/test-coverage.md",
      },
    ],
    artifacts: [
      {
        name: "coverage-report.txt",
        path: "[REDACTED]/validation-evidence/T001/round-2/coverage-report.txt",
        type: "text/plain",
      },
    ],
  },
];

const mockQA: TaskQADetailResponse = {
  qaId: "QA-001",
  taskId: "T001",
  sessionId: "session-1",
  round: 2,
  state: "done",
  verdict: "passed",
  validators: ["code-review", "test-coverage"],
  evidence: mockRoundEvidence,
  stateHistory: [
    { state: "waiting", timestamp: "2025-01-01T10:00:00Z" },
    { state: "todo", timestamp: "2025-01-01T12:00:00Z" },
    { state: "wip", timestamp: "2025-01-02T09:00:00Z" },
    { state: "done", timestamp: "2025-01-02T15:00:00Z" },
  ],
  createdAt: "2025-01-01T10:00:00Z",
  updatedAt: "2025-01-02T15:00:00Z",
};

describe("TaskQAPanel", () => {
  describe("Loading state", () => {
    it("displays loading indicator when isLoading is true", () => {
      render(<TaskQAPanel qa={null} isLoading={true} />);

      expect(screen.getByTestId("qa-panel-loading")).toBeInTheDocument();
      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });
  });

  describe("Error state", () => {
    it("displays error message when error is provided", () => {
      const error = new Error("Failed to fetch QA data");
      render(<TaskQAPanel qa={null} error={error} />);

      expect(screen.getByTestId("qa-panel-error")).toBeInTheDocument();
      expect(screen.getByText(/failed to fetch qa data/i)).toBeInTheDocument();
    });
  });

  describe("Empty state", () => {
    it("displays empty state when qa is null and not loading", () => {
      render(<TaskQAPanel qa={null} isLoading={false} />);

      expect(screen.getByTestId("qa-panel-empty")).toBeInTheDocument();
      expect(screen.getByText(/no qa record/i)).toBeInTheDocument();
    });
  });

  describe("QA Panel content", () => {
    it("renders panel with QA ID and state", () => {
      render(<TaskQAPanel qa={mockQA} />);

      expect(screen.getByText("QA-001")).toBeInTheDocument();
      expect(screen.getByText("done")).toBeInTheDocument();
    });

    it("displays current round number", () => {
      render(<TaskQAPanel qa={mockQA} />);

      // Multiple elements have "Round 2", just verify at least one exists
      const roundElements = screen.getAllByText(/round 2/i);
      expect(roundElements.length).toBeGreaterThan(0);
    });

    it("displays verdict badge with correct color for passed", () => {
      render(<TaskQAPanel qa={mockQA} />);

      const verdictBadge = screen.getByTestId("verdict-badge");
      expect(verdictBadge).toBeInTheDocument();
      expect(verdictBadge).toHaveTextContent("passed");
      expect(verdictBadge).toHaveClass("bg-green-100");
    });

    it("displays verdict badge with correct color for rejected", () => {
      const rejectedQA: TaskQADetailResponse = {
        ...mockQA,
        verdict: "rejected",
      };
      render(<TaskQAPanel qa={rejectedQA} />);

      const verdictBadge = screen.getByTestId("verdict-badge");
      expect(verdictBadge).toHaveTextContent("rejected");
      expect(verdictBadge).toHaveClass("bg-red-100");
    });

    it("displays verdict badge with correct color for in_progress", () => {
      const inProgressQA: TaskQADetailResponse = {
        ...mockQA,
        verdict: "in_progress",
      };
      render(<TaskQAPanel qa={inProgressQA} />);

      const verdictBadge = screen.getByTestId("verdict-badge");
      expect(verdictBadge).toHaveTextContent("in_progress");
      expect(verdictBadge).toHaveClass("bg-yellow-100");
    });

    it("displays list of validators", () => {
      render(<TaskQAPanel qa={mockQA} />);

      // Multiple elements contain validator names (header and timeline)
      // Just verify they exist
      const codeReviewElements = screen.getAllByText("code-review");
      const testCoverageElements = screen.getAllByText("test-coverage");
      expect(codeReviewElements.length).toBeGreaterThan(0);
      expect(testCoverageElements.length).toBeGreaterThan(0);
    });
  });

  describe("Rounds timeline", () => {
    it("renders all rounds in the timeline", () => {
      render(<TaskQAPanel qa={mockQA} />);

      // Use getByRole to find the round buttons
      expect(
        screen.getByRole("button", { name: /round 1/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /round 2/i }),
      ).toBeInTheDocument();
    });

    it("shows current round as expanded by default", () => {
      render(<TaskQAPanel qa={mockQA} />);

      // Round 2 (current) should show its details by default
      expect(screen.getByText("Fixed error handling")).toBeInTheDocument();
    });

    it("allows expanding and collapsing rounds", () => {
      render(<TaskQAPanel qa={mockQA} />);

      // Click on Round 1 to expand it
      const round1Header = screen.getByRole("button", { name: /round 1/i });
      fireEvent.click(round1Header);

      // Now Round 1 details should be visible
      expect(
        screen.getByText("Initial implementation bundle"),
      ).toBeInTheDocument();
    });
  });

  describe("Validator reports", () => {
    it("displays validator reports for expanded round", () => {
      render(<TaskQAPanel qa={mockQA} />);

      // Round 2 is expanded by default
      expect(screen.getByText("All checks passed")).toBeInTheDocument();
      expect(screen.getByText("Coverage at 95%")).toBeInTheDocument();
    });

    it("shows failure reason with red indicator for failed validators", () => {
      render(<TaskQAPanel qa={mockQA} />);

      // Expand Round 1 which has a failed validator
      const round1Header = screen.getByRole("button", { name: /round 1/i });
      fireEvent.click(round1Header);

      const failureReason = screen.getByText(
        "Missing error handling in API calls",
      );
      expect(failureReason).toBeInTheDocument();

      // Find the parent container and check for red styling
      const failBadge = screen.getByTestId(
        "validator-badge-code-review-round-1",
      );
      expect(failBadge).toHaveClass("bg-red-100");
    });

    it("shows pass indicator for successful validators", () => {
      render(<TaskQAPanel qa={mockQA} />);

      // Round 2 is expanded by default with passing validators
      const passBadge = screen.getByTestId(
        "validator-badge-code-review-round-2",
      );
      expect(passBadge).toHaveClass("bg-green-100");
    });
  });

  describe("Evidence artifacts", () => {
    it("displays evidence artifacts as links", () => {
      render(<TaskQAPanel qa={mockQA} />);

      // Round 2 is expanded by default
      const artifactLink = screen.getByRole("link", {
        name: /coverage-report\.txt/i,
      });
      expect(artifactLink).toBeInTheDocument();
    });

    it("shows redacted paths for artifacts", () => {
      render(<TaskQAPanel qa={mockQA} />);

      // Paths should be redacted (show [REDACTED] prefix)
      // Multiple elements will contain [REDACTED], just verify at least one exists
      const redactedElements = screen.getAllByText(/\[REDACTED\]/);
      expect(redactedElements.length).toBeGreaterThan(0);
    });
  });

  describe("Accessibility", () => {
    it("has accessible section heading", () => {
      render(<TaskQAPanel qa={mockQA} />);

      expect(
        screen.getByRole("heading", { name: /qa validation/i }),
      ).toBeInTheDocument();
    });

    it("round toggle buttons have aria-expanded attribute", () => {
      render(<TaskQAPanel qa={mockQA} />);

      const round1Header = screen.getByRole("button", { name: /round 1/i });
      expect(round1Header).toHaveAttribute("aria-expanded", "false");

      const round2Header = screen.getByRole("button", { name: /round 2/i });
      expect(round2Header).toHaveAttribute("aria-expanded", "true");
    });

    it("supports keyboard navigation for round expansion", () => {
      render(<TaskQAPanel qa={mockQA} />);

      const round1Header = screen.getByRole("button", { name: /round 1/i });
      round1Header.focus();

      // Press Enter to expand
      fireEvent.keyDown(round1Header, { key: "Enter" });
      expect(round1Header).toHaveAttribute("aria-expanded", "true");

      // Press Space to collapse
      fireEvent.keyDown(round1Header, { key: " " });
      expect(round1Header).toHaveAttribute("aria-expanded", "false");
    });
  });
});
