import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { PreviewConfirmDialog } from "./PreviewConfirmDialog";
import type { GuardFailure, GuardWarning } from "./types";

describe("PreviewConfirmDialog", () => {
  const defaultProps = {
    title: "Confirm Action",
    open: true,
    onClose: vi.fn(),
    onConfirm: vi.fn(),
    loading: false,
    preview: { message: "Are you sure you want to proceed?" },
    guardFailures: [] as GuardFailure[],
    guardWarnings: [] as GuardWarning[],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("rendering", () => {
    it("renders nothing when open is false", () => {
      const { container } = render(
        <PreviewConfirmDialog {...defaultProps} open={false} />,
      );
      expect(container.querySelector("dialog")).toBeNull();
    });

    it("renders dialog when open is true", () => {
      render(<PreviewConfirmDialog {...defaultProps} />);
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    it("displays the title", () => {
      render(<PreviewConfirmDialog {...defaultProps} />);
      expect(screen.getByText("Confirm Action")).toBeInTheDocument();
    });

    it("renders preview content", () => {
      render(<PreviewConfirmDialog {...defaultProps} />);
      expect(
        screen.getByText("Are you sure you want to proceed?"),
      ).toBeInTheDocument();
    });

    it("renders custom preview component when provided", () => {
      const customPreview = (
        <div data-testid="custom-preview">Custom Preview</div>
      );
      render(
        <PreviewConfirmDialog
          {...defaultProps}
          previewComponent={customPreview}
        />,
      );
      expect(screen.getByTestId("custom-preview")).toBeInTheDocument();
    });
  });

  describe("buttons", () => {
    it("displays confirm and cancel buttons in preview mode", () => {
      render(<PreviewConfirmDialog {...defaultProps} />);
      expect(
        screen.getByRole("button", { name: /confirm/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /cancel/i }),
      ).toBeInTheDocument();
    });

    it("calls onClose when cancel button is clicked", async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();
      render(<PreviewConfirmDialog {...defaultProps} onClose={onClose} />);

      await user.click(screen.getByRole("button", { name: /cancel/i }));
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it("calls onConfirm when confirm button is clicked", async () => {
      const user = userEvent.setup();
      const onConfirm = vi.fn().mockResolvedValue(undefined);
      render(<PreviewConfirmDialog {...defaultProps} onConfirm={onConfirm} />);

      await user.click(screen.getByRole("button", { name: /confirm/i }));
      expect(onConfirm).toHaveBeenCalledTimes(1);
    });

    it("disables confirm button when loading", () => {
      render(<PreviewConfirmDialog {...defaultProps} loading={true} />);
      expect(screen.getByRole("button", { name: /confirm/i })).toBeDisabled();
    });

    it("disables cancel button when loading", () => {
      render(<PreviewConfirmDialog {...defaultProps} loading={true} />);
      expect(screen.getByRole("button", { name: /cancel/i })).toBeDisabled();
    });
  });

  describe("loading state", () => {
    it("shows loading spinner when loading is true", () => {
      render(<PreviewConfirmDialog {...defaultProps} loading={true} />);
      expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
    });

    it("shows loading text on confirm button when loading", () => {
      render(<PreviewConfirmDialog {...defaultProps} loading={true} />);
      expect(screen.getByText(/confirming/i)).toBeInTheDocument();
    });
  });

  describe("guard failures", () => {
    it("displays guard failures when present", () => {
      const failures: GuardFailure[] = [
        { guard: "evidence_required", reason: "Missing evidence" },
      ];
      render(
        <PreviewConfirmDialog {...defaultProps} guardFailures={failures} />,
      );
      expect(screen.getByText("Missing evidence")).toBeInTheDocument();
    });

    it("disables confirm button when there are guard failures", () => {
      const failures: GuardFailure[] = [
        { guard: "evidence_required", reason: "Missing evidence" },
      ];
      render(
        <PreviewConfirmDialog {...defaultProps} guardFailures={failures} />,
      );
      expect(screen.getByRole("button", { name: /confirm/i })).toBeDisabled();
    });

    it("shows guard failure alert component", () => {
      const failures: GuardFailure[] = [
        { guard: "evidence_required", reason: "Missing evidence" },
      ];
      render(
        <PreviewConfirmDialog {...defaultProps} guardFailures={failures} />,
      );
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  describe("guard warnings", () => {
    it("displays guard warnings when present", () => {
      const warnings: GuardWarning[] = [
        { guard: "session_scope", message: "Task is outside current session" },
      ];
      render(
        <PreviewConfirmDialog {...defaultProps} guardWarnings={warnings} />,
      );
      expect(
        screen.getByText("Task is outside current session"),
      ).toBeInTheDocument();
    });

    it("does not disable confirm button for warnings only", () => {
      const warnings: GuardWarning[] = [
        { guard: "session_scope", message: "Warning message" },
      ];
      render(
        <PreviewConfirmDialog {...defaultProps} guardWarnings={warnings} />,
      );
      expect(
        screen.getByRole("button", { name: /confirm/i }),
      ).not.toBeDisabled();
    });

    it("shows warning styling for guard warnings", () => {
      const warnings: GuardWarning[] = [
        { guard: "session_scope", message: "Warning message" },
      ];
      render(
        <PreviewConfirmDialog {...defaultProps} guardWarnings={warnings} />,
      );
      expect(screen.getByTestId("guard-warnings")).toHaveClass("bg-yellow-50");
    });
  });

  describe("accessibility", () => {
    it("has accessible dialog role", () => {
      render(<PreviewConfirmDialog {...defaultProps} />);
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    it("has aria-labelledby pointing to title", () => {
      render(<PreviewConfirmDialog {...defaultProps} />);
      const dialog = screen.getByRole("dialog");
      expect(dialog).toHaveAttribute("aria-labelledby");
    });

    it("has aria-modal attribute", () => {
      render(<PreviewConfirmDialog {...defaultProps} />);
      const dialog = screen.getByRole("dialog");
      expect(dialog).toHaveAttribute("aria-modal", "true");
    });

    it("closes on Escape key press", async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();
      render(<PreviewConfirmDialog {...defaultProps} onClose={onClose} />);

      await user.keyboard("{Escape}");
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it("contains focusable elements for keyboard navigation", () => {
      render(<PreviewConfirmDialog {...defaultProps} />);

      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      const confirmButton = screen.getByRole("button", { name: /confirm/i });

      // Verify both buttons are focusable
      expect(cancelButton).not.toHaveAttribute("tabindex", "-1");
      expect(confirmButton).not.toHaveAttribute("tabindex", "-1");

      // Verify buttons can receive focus
      confirmButton.focus();
      expect(confirmButton).toHaveFocus();

      cancelButton.focus();
      expect(cancelButton).toHaveFocus();
    });
  });

  describe("backdrop", () => {
    it("renders backdrop overlay", () => {
      render(<PreviewConfirmDialog {...defaultProps} />);
      expect(screen.getByTestId("dialog-backdrop")).toBeInTheDocument();
    });

    it("closes dialog when backdrop is clicked", async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();
      render(<PreviewConfirmDialog {...defaultProps} onClose={onClose} />);

      await user.click(screen.getByTestId("dialog-backdrop"));
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it("does not close dialog when clicking inside dialog content", async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();
      render(<PreviewConfirmDialog {...defaultProps} onClose={onClose} />);

      await user.click(screen.getByText("Confirm Action"));
      expect(onClose).not.toHaveBeenCalled();
    });
  });

  describe("success state", () => {
    it("displays success message when provided", () => {
      render(
        <PreviewConfirmDialog
          {...defaultProps}
          successMessage="Action completed successfully!"
        />,
      );
      expect(
        screen.getByText("Action completed successfully!"),
      ).toBeInTheDocument();
    });

    it("auto-closes after success when configured", async () => {
      vi.useFakeTimers();
      const onClose = vi.fn();
      render(
        <PreviewConfirmDialog
          {...defaultProps}
          onClose={onClose}
          successMessage="Success!"
          autoCloseOnSuccess={true}
        />,
      );

      vi.advanceTimersByTime(1500);
      expect(onClose).toHaveBeenCalledTimes(1);
      vi.useRealTimers();
    });
  });

  describe("custom buttons", () => {
    it("uses custom confirm text when provided", () => {
      render(<PreviewConfirmDialog {...defaultProps} confirmText="Submit" />);
      expect(
        screen.getByRole("button", { name: "Submit" }),
      ).toBeInTheDocument();
    });

    it("uses custom cancel text when provided", () => {
      render(<PreviewConfirmDialog {...defaultProps} cancelText="Dismiss" />);
      expect(
        screen.getByRole("button", { name: "Dismiss" }),
      ).toBeInTheDocument();
    });
  });
});
