import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { GuardFailureAlert } from "./GuardFailureAlert";
import type { GuardFailure } from "./types";

describe("GuardFailureAlert", () => {
  describe("rendering", () => {
    it("renders nothing when failures array is empty", () => {
      const { container } = render(<GuardFailureAlert failures={[]} />);
      expect(container.firstChild).toBeNull();
    });

    it("renders alert banner when there are failures", () => {
      const failures: GuardFailure[] = [
        { guard: "evidence_required", reason: "Missing test evidence" },
      ];
      render(<GuardFailureAlert failures={failures} />);

      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    it("displays each guard failure with its reason", () => {
      const failures: GuardFailure[] = [
        { guard: "evidence_required", reason: "Missing test evidence" },
        { guard: "dependencies_met", reason: "Task T001 is not complete" },
      ];
      render(<GuardFailureAlert failures={failures} />);

      expect(screen.getByText("Missing test evidence")).toBeInTheDocument();
      expect(
        screen.getByText("Task T001 is not complete"),
      ).toBeInTheDocument();
    });

    it("displays guard name for each failure", () => {
      const failures: GuardFailure[] = [
        { guard: "evidence_required", reason: "Missing test evidence" },
      ];
      render(<GuardFailureAlert failures={failures} />);

      expect(screen.getByText("evidence_required")).toBeInTheDocument();
    });
  });

  describe("styling", () => {
    it("has error/red styling for the alert", () => {
      const failures: GuardFailure[] = [
        { guard: "test_guard", reason: "Test reason" },
      ];
      render(<GuardFailureAlert failures={failures} />);

      const alert = screen.getByRole("alert");
      expect(alert).toHaveClass("bg-red-50");
      expect(alert).toHaveClass("border-red-200");
    });

    it("displays error icon", () => {
      const failures: GuardFailure[] = [
        { guard: "test_guard", reason: "Test reason" },
      ];
      render(<GuardFailureAlert failures={failures} />);

      // Icon should be present but hidden from screen readers
      const icon = screen.getByTestId("guard-failure-icon");
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveAttribute("aria-hidden", "true");
    });
  });

  describe("accessibility", () => {
    it("has role=alert for screen reader announcement", () => {
      const failures: GuardFailure[] = [
        { guard: "test_guard", reason: "Test reason" },
      ];
      render(<GuardFailureAlert failures={failures} />);

      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    it("renders failures as a list for screen readers", () => {
      const failures: GuardFailure[] = [
        { guard: "guard1", reason: "Reason 1" },
        { guard: "guard2", reason: "Reason 2" },
      ];
      render(<GuardFailureAlert failures={failures} />);

      expect(screen.getByRole("list")).toBeInTheDocument();
      expect(screen.getAllByRole("listitem")).toHaveLength(2);
    });

    it("has descriptive heading", () => {
      const failures: GuardFailure[] = [
        { guard: "test_guard", reason: "Test reason" },
      ];
      render(<GuardFailureAlert failures={failures} />);

      expect(
        screen.getByText(/action blocked|guard failure/i),
      ).toBeInTheDocument();
    });
  });

  describe("with title prop", () => {
    it("displays custom title when provided", () => {
      const failures: GuardFailure[] = [
        { guard: "test_guard", reason: "Test reason" },
      ];
      render(
        <GuardFailureAlert failures={failures} title="Custom Error Title" />,
      );

      expect(screen.getByText("Custom Error Title")).toBeInTheDocument();
    });
  });
});
