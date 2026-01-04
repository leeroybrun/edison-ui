import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RoundTimeline } from "./RoundTimeline";
import type { RoundEvidence } from "./types";

const mockEvidence: RoundEvidence[] = [
  {
    roundNumber: 1,
    bundleSummary: "Initial implementation bundle",
    implementationReport: "## Summary\nInitial implementation completed",
    validatorReports: [
      {
        validatorId: "code-review",
        verdict: "fail",
        reason: "Missing error handling",
        reportPath: "[REDACTED]/round-1/code-review.md",
      },
    ],
    artifacts: [
      {
        name: "coverage.txt",
        path: "[REDACTED]/round-1/coverage.txt",
        type: "text/plain",
      },
    ],
  },
  {
    roundNumber: 2,
    bundleSummary: "Fixed issues from round 1",
    implementationReport: "## Summary\nAdded error handling",
    validatorReports: [
      {
        validatorId: "code-review",
        verdict: "pass",
        reason: "All checks passed",
        reportPath: "[REDACTED]/round-2/code-review.md",
      },
    ],
    artifacts: [],
  },
  {
    roundNumber: 3,
    bundleSummary: "Final adjustments",
    implementationReport: null,
    validatorReports: [
      {
        validatorId: "code-review",
        verdict: "pass",
        reason: "Approved",
        reportPath: "[REDACTED]/round-3/code-review.md",
      },
      {
        validatorId: "test-coverage",
        verdict: "pass",
        reason: "Coverage 98%",
        reportPath: "[REDACTED]/round-3/test-coverage.md",
      },
    ],
    artifacts: [
      {
        name: "final-coverage.txt",
        path: "[REDACTED]/round-3/final-coverage.txt",
        type: "text/plain",
      },
    ],
  },
];

describe("RoundTimeline", () => {
  describe("Timeline rendering", () => {
    it("renders all rounds in order", () => {
      render(
        <RoundTimeline
          evidence={mockEvidence}
          currentRound={3}
          verdict="passed"
        />
      );

      expect(screen.getByText("Round 1")).toBeInTheDocument();
      expect(screen.getByText("Round 2")).toBeInTheDocument();
      expect(screen.getByText("Round 3")).toBeInTheDocument();
    });

    it("renders timeline connector between rounds", () => {
      render(
        <RoundTimeline
          evidence={mockEvidence}
          currentRound={3}
          verdict="passed"
        />
      );

      // Timeline should have visual connectors
      const connectors = screen.getAllByTestId("timeline-connector");
      // Should have N-1 connectors for N rounds
      expect(connectors).toHaveLength(2);
    });

    it("highlights current round", () => {
      render(
        <RoundTimeline
          evidence={mockEvidence}
          currentRound={3}
          verdict="passed"
        />
      );

      const currentRoundIndicator = screen.getByTestId("round-indicator-3");
      expect(currentRoundIndicator).toHaveClass("ring-2");
    });

    it("shows pass/fail indicator on each round", () => {
      render(
        <RoundTimeline
          evidence={mockEvidence}
          currentRound={3}
          verdict="passed"
        />
      );

      // Round 1 failed (has a failing validator)
      const round1Indicator = screen.getByTestId("round-indicator-1");
      expect(round1Indicator).toHaveClass("bg-red-500");

      // Round 2 passed (all validators passed)
      const round2Indicator = screen.getByTestId("round-indicator-2");
      expect(round2Indicator).toHaveClass("bg-green-500");

      // Round 3 passed (all validators passed)
      const round3Indicator = screen.getByTestId("round-indicator-3");
      expect(round3Indicator).toHaveClass("bg-green-500");
    });
  });

  describe("Empty state", () => {
    it("shows empty message when no evidence", () => {
      render(
        <RoundTimeline evidence={[]} currentRound={0} verdict={null} />
      );

      expect(screen.getByText(/no validation rounds/i)).toBeInTheDocument();
    });
  });

  describe("Expand/Collapse", () => {
    it("expands current round by default", () => {
      render(
        <RoundTimeline
          evidence={mockEvidence}
          currentRound={3}
          verdict="passed"
        />
      );

      // Round 3 content should be visible
      expect(screen.getByText("Final adjustments")).toBeInTheDocument();
    });

    it("collapses non-current rounds by default", () => {
      render(
        <RoundTimeline
          evidence={mockEvidence}
          currentRound={3}
          verdict="passed"
        />
      );

      // Round 1 content should not be visible initially
      expect(
        screen.queryByText("Initial implementation bundle")
      ).not.toBeInTheDocument();
    });

    it("toggles round expansion on click", () => {
      render(
        <RoundTimeline
          evidence={mockEvidence}
          currentRound={3}
          verdict="passed"
        />
      );

      // Expand Round 1
      const round1Button = screen.getByRole("button", { name: /round 1/i });
      fireEvent.click(round1Button);

      expect(
        screen.getByText("Initial implementation bundle")
      ).toBeInTheDocument();

      // Collapse Round 1
      fireEvent.click(round1Button);

      expect(
        screen.queryByText("Initial implementation bundle")
      ).not.toBeInTheDocument();
    });
  });

  describe("Round details", () => {
    it("shows bundle summary when expanded", () => {
      render(
        <RoundTimeline
          evidence={mockEvidence}
          currentRound={3}
          verdict="passed"
        />
      );

      expect(screen.getByText("Final adjustments")).toBeInTheDocument();
    });

    it("shows validator reports when expanded", () => {
      render(
        <RoundTimeline
          evidence={mockEvidence}
          currentRound={3}
          verdict="passed"
        />
      );

      expect(screen.getByText("code-review")).toBeInTheDocument();
      expect(screen.getByText("Approved")).toBeInTheDocument();
    });

    it("shows artifacts when expanded", () => {
      render(
        <RoundTimeline
          evidence={mockEvidence}
          currentRound={3}
          verdict="passed"
        />
      );

      expect(screen.getByText("final-coverage.txt")).toBeInTheDocument();
    });

    it("shows implementation report when available", () => {
      render(
        <RoundTimeline
          evidence={mockEvidence}
          currentRound={2}
          verdict="passed"
        />
      );

      // Round 2 is current and expanded by default
      expect(
        screen.getByText(/added error handling/i)
      ).toBeInTheDocument();
    });

    it("handles null implementation report gracefully", () => {
      render(
        <RoundTimeline
          evidence={mockEvidence}
          currentRound={3}
          verdict="passed"
        />
      );

      // Round 3 has null implementationReport, should not crash
      expect(screen.getByText("Final adjustments")).toBeInTheDocument();
      // Should not show "Implementation Report" section for round 3
      expect(
        screen.queryByTestId("implementation-report-3")
      ).not.toBeInTheDocument();
    });
  });

  describe("Validator status", () => {
    it("shows pass badge for passing validators", () => {
      render(
        <RoundTimeline
          evidence={mockEvidence}
          currentRound={3}
          verdict="passed"
        />
      );

      const passBadges = screen.getAllByTestId(/validator-badge.*round-3/);
      passBadges.forEach((badge) => {
        expect(badge).toHaveClass("bg-green-100");
      });
    });

    it("shows fail badge for failing validators", () => {
      render(
        <RoundTimeline
          evidence={mockEvidence}
          currentRound={3}
          verdict="passed"
        />
      );

      // Expand Round 1
      const round1Button = screen.getByRole("button", { name: /round 1/i });
      fireEvent.click(round1Button);

      const failBadge = screen.getByTestId("validator-badge-code-review-round-1");
      expect(failBadge).toHaveClass("bg-red-100");
    });

    it("displays failure reason prominently", () => {
      render(
        <RoundTimeline
          evidence={mockEvidence}
          currentRound={3}
          verdict="passed"
        />
      );

      // Expand Round 1
      const round1Button = screen.getByRole("button", { name: /round 1/i });
      fireEvent.click(round1Button);

      expect(screen.getByText("Missing error handling")).toBeInTheDocument();
    });
  });

  describe("Accessibility", () => {
    it("has accessible timeline landmark", () => {
      render(
        <RoundTimeline
          evidence={mockEvidence}
          currentRound={3}
          verdict="passed"
        />
      );

      // Should have at least one list element (the timeline)
      const lists = screen.getAllByRole("list");
      expect(lists.length).toBeGreaterThan(0);
    });

    it("round buttons have aria-expanded", () => {
      render(
        <RoundTimeline
          evidence={mockEvidence}
          currentRound={3}
          verdict="passed"
        />
      );

      const round1Button = screen.getByRole("button", { name: /round 1/i });
      expect(round1Button).toHaveAttribute("aria-expanded", "false");

      const round3Button = screen.getByRole("button", { name: /round 3/i });
      expect(round3Button).toHaveAttribute("aria-expanded", "true");
    });

    it("supports keyboard navigation", () => {
      render(
        <RoundTimeline
          evidence={mockEvidence}
          currentRound={3}
          verdict="passed"
        />
      );

      const round1Button = screen.getByRole("button", { name: /round 1/i });
      round1Button.focus();

      // Enter should expand
      fireEvent.keyDown(round1Button, { key: "Enter" });
      expect(round1Button).toHaveAttribute("aria-expanded", "true");
    });
  });
});
