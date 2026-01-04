import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { QACard } from "./QACard";
import type { QARecord } from "./types";

const mockQA: QARecord = {
  qaId: "QA001",
  taskId: "T001",
  sessionId: "session-1",
  round: 1,
  state: "done",
  verdict: "passed",
  validators: ["validator-1"],
  createdAt: "2025-01-01T10:00:00Z",
  updatedAt: "2025-01-02T15:30:00Z",
};

describe("QACard", () => {
  describe("Basic Rendering", () => {
    it("renders QA ID", () => {
      render(<QACard qa={mockQA} />);

      expect(screen.getByText("QA001")).toBeInTheDocument();
    });

    it("renders task ID", () => {
      render(<QACard qa={mockQA} />);

      expect(screen.getByText("T001")).toBeInTheDocument();
    });

    it("renders state badge", () => {
      render(<QACard qa={mockQA} />);

      const stateBadge = screen.getByText("done");
      expect(stateBadge).toBeInTheDocument();
      expect(stateBadge).toHaveAttribute("data-state", "done");
    });

    it("renders verdict badge for passed", () => {
      render(<QACard qa={mockQA} />);

      expect(screen.getByText("passed")).toBeInTheDocument();
    });

    it("renders verdict badge for rejected", () => {
      const rejectedQA: QARecord = {
        ...mockQA,
        verdict: "rejected",
      };
      render(<QACard qa={rejectedQA} />);

      expect(screen.getByText("rejected")).toBeInTheDocument();
    });

    it("renders verdict badge for in_progress", () => {
      const inProgressQA: QARecord = {
        ...mockQA,
        verdict: "in_progress",
      };
      render(<QACard qa={inProgressQA} />);

      expect(screen.getByText("in_progress")).toBeInTheDocument();
    });

    it("renders no verdict when null", () => {
      const noVerdictQA: QARecord = {
        ...mockQA,
        verdict: null,
      };
      render(<QACard qa={noVerdictQA} />);

      // Should not have any verdict badge
      expect(screen.queryByText("passed")).not.toBeInTheDocument();
      expect(screen.queryByText("rejected")).not.toBeInTheDocument();
      expect(screen.queryByText("in_progress")).not.toBeInTheDocument();
    });

    it("renders round number", () => {
      const multiRoundQA: QARecord = {
        ...mockQA,
        round: 3,
      };
      render(<QACard qa={multiRoundQA} />);

      expect(screen.getByText(/round 3/i)).toBeInTheDocument();
    });

    it("renders validators list", () => {
      const multiValidatorQA: QARecord = {
        ...mockQA,
        validators: ["validator-1", "validator-2"],
      };
      render(<QACard qa={multiValidatorQA} />);

      expect(screen.getByText("validator-1")).toBeInTheDocument();
      expect(screen.getByText("validator-2")).toBeInTheDocument();
    });

    it("renders no validators message when empty", () => {
      const noValidatorsQA: QARecord = {
        ...mockQA,
        validators: [],
      };
      render(<QACard qa={noValidatorsQA} />);

      expect(screen.getByText(/no validators/i)).toBeInTheDocument();
    });
  });

  describe("Session ID", () => {
    it("renders session ID when present", () => {
      render(<QACard qa={mockQA} />);

      expect(screen.getByText("session-1")).toBeInTheDocument();
    });

    it("does not show session when null", () => {
      const unscopedQA: QARecord = {
        ...mockQA,
        sessionId: null,
      };
      render(<QACard qa={unscopedQA} />);

      expect(screen.queryByText("session-1")).not.toBeInTheDocument();
    });
  });

  describe("Selection State", () => {
    it("applies selected styling when isSelected is true", () => {
      render(<QACard isSelected qa={mockQA} />);

      const article = screen.getByRole("article");
      expect(article).toHaveAttribute("data-selected", "true");
    });

    it("does not apply selected styling when isSelected is false", () => {
      render(<QACard isSelected={false} qa={mockQA} />);

      const article = screen.getByRole("article");
      expect(article).not.toHaveAttribute("data-selected");
    });
  });

  describe("Click Interaction", () => {
    it("calls onClick when clicked", () => {
      const handleClick = vi.fn();
      render(<QACard onClick={handleClick} qa={mockQA} />);

      fireEvent.click(screen.getByRole("article"));

      expect(handleClick).toHaveBeenCalledWith("QA001");
    });

    it("calls onClick on Enter key", () => {
      const handleClick = vi.fn();
      render(<QACard onClick={handleClick} qa={mockQA} />);

      fireEvent.keyDown(screen.getByRole("article"), { key: "Enter" });

      expect(handleClick).toHaveBeenCalledWith("QA001");
    });

    it("calls onClick on Space key", () => {
      const handleClick = vi.fn();
      render(<QACard onClick={handleClick} qa={mockQA} />);

      fireEvent.keyDown(screen.getByRole("article"), { key: " " });

      expect(handleClick).toHaveBeenCalledWith("QA001");
    });

    it("has tabIndex when onClick is provided", () => {
      const handleClick = vi.fn();
      render(<QACard onClick={handleClick} qa={mockQA} />);

      expect(screen.getByRole("article")).toHaveAttribute("tabindex", "0");
    });

    it("does not have tabIndex when onClick is not provided", () => {
      render(<QACard qa={mockQA} />);

      expect(screen.getByRole("article")).not.toHaveAttribute("tabindex");
    });
  });

  describe("Verdict Badge Colors", () => {
    it("applies green styling for passed verdict", () => {
      render(<QACard qa={mockQA} />);

      const verdictBadge = screen.getByTestId("verdict-badge");
      expect(verdictBadge).toHaveClass("bg-green-100");
    });

    it("applies red styling for rejected verdict", () => {
      const rejectedQA: QARecord = {
        ...mockQA,
        verdict: "rejected",
      };
      render(<QACard qa={rejectedQA} />);

      const verdictBadge = screen.getByTestId("verdict-badge");
      expect(verdictBadge).toHaveClass("bg-red-100");
    });

    it("applies blue styling for in_progress verdict", () => {
      const inProgressQA: QARecord = {
        ...mockQA,
        verdict: "in_progress",
      };
      render(<QACard qa={inProgressQA} />);

      const verdictBadge = screen.getByTestId("verdict-badge");
      expect(verdictBadge).toHaveClass("bg-blue-100");
    });
  });

  describe("State Badge Colors", () => {
    it("applies correct color for waiting state", () => {
      const waitingQA: QARecord = {
        ...mockQA,
        state: "waiting",
      };
      render(<QACard qa={waitingQA} />);

      const stateBadge = screen.getByText("waiting");
      expect(stateBadge).toHaveClass("bg-yellow-100");
    });

    it("applies correct color for todo state", () => {
      const todoQA: QARecord = {
        ...mockQA,
        state: "todo",
      };
      render(<QACard qa={todoQA} />);

      const stateBadge = screen.getByText("todo");
      expect(stateBadge).toHaveClass("bg-gray-100");
    });

    it("applies correct color for wip state", () => {
      const wipQA: QARecord = {
        ...mockQA,
        state: "wip",
      };
      render(<QACard qa={wipQA} />);

      const stateBadge = screen.getByText("wip");
      expect(stateBadge).toHaveClass("bg-blue-100");
    });

    it("applies correct color for done state", () => {
      render(<QACard qa={mockQA} />);

      const stateBadge = screen.getByText("done");
      expect(stateBadge).toHaveClass("bg-green-100");
    });

    it("applies correct color for validated state", () => {
      const validatedQA: QARecord = {
        ...mockQA,
        state: "validated",
      };
      render(<QACard qa={validatedQA} />);

      const stateBadge = screen.getByText("validated");
      expect(stateBadge).toHaveClass("bg-purple-100");
    });
  });
});
