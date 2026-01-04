import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { TaskTransitionDialog } from "./TaskTransitionDialog";

// Mock fetch for API calls
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe("TaskTransitionDialog", () => {
  const defaultProps = {
    taskId: "T001",
    projectId: "project-1",
    toState: "wip",
    open: true,
    onClose: vi.fn(),
    onSuccess: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe("preview loading", () => {
    it("renders nothing when open is false", () => {
      const { container } = render(
        <TaskTransitionDialog {...defaultProps} open={false} />,
      );
      expect(container.querySelector("[role='dialog']")).toBeNull();
    });

    it("fetches preview when opened", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          valid: true,
          currentState: "todo",
          toState: "wip",
          guardFailures: [],
          guardWarnings: [],
        }),
      });

      render(<TaskTransitionDialog {...defaultProps} />);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining("/api/v1/projects/project-1/tasks/T001/transition/preview"),
          expect.objectContaining({
            method: "POST",
            headers: expect.objectContaining({
              "Content-Type": "application/json",
            }),
            body: JSON.stringify({ toState: "wip" }),
          }),
        );
      });
    });

    it("shows loading state while fetching preview", async () => {
      mockFetch.mockImplementation(
        () => new Promise(() => {}), // Never resolves
      );

      render(<TaskTransitionDialog {...defaultProps} />);
      expect(screen.getByTestId("preview-loading")).toBeInTheDocument();
    });
  });

  describe("preview display", () => {
    it("displays transition preview with from and to states", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          valid: true,
          currentState: "todo",
          toState: "wip",
          guardFailures: [],
          guardWarnings: [],
        }),
      });

      render(<TaskTransitionDialog {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText(/todo/i)).toBeInTheDocument();
        expect(screen.getByText(/wip/i)).toBeInTheDocument();
      });
    });

    it("shows task ID in title", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          valid: true,
          currentState: "todo",
          toState: "wip",
          guardFailures: [],
          guardWarnings: [],
        }),
      });

      render(<TaskTransitionDialog {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText(/T001/)).toBeInTheDocument();
      });
    });
  });

  describe("guard failures", () => {
    it("displays guard failures when transition is blocked", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          valid: false,
          currentState: "wip",
          toState: "done",
          guardFailures: [
            { guard: "evidence_required", reason: "Missing test evidence" },
          ],
          guardWarnings: [],
        }),
      });

      render(<TaskTransitionDialog {...defaultProps} toState="done" />);

      await waitFor(() => {
        expect(screen.getByText("Missing test evidence")).toBeInTheDocument();
      });
    });

    it("disables confirm button when there are guard failures", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          valid: false,
          currentState: "wip",
          toState: "done",
          guardFailures: [
            { guard: "evidence_required", reason: "Missing test evidence" },
          ],
          guardWarnings: [],
        }),
      });

      render(<TaskTransitionDialog {...defaultProps} toState="done" />);

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /confirm/i }),
        ).toBeDisabled();
      });
    });
  });

  describe("guard warnings", () => {
    it("displays guard warnings", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          valid: true,
          currentState: "todo",
          toState: "wip",
          guardFailures: [],
          guardWarnings: [
            { guard: "session_scope", message: "Task is outside current session" },
          ],
        }),
      });

      render(<TaskTransitionDialog {...defaultProps} />);

      await waitFor(() => {
        expect(
          screen.getByText("Task is outside current session"),
        ).toBeInTheDocument();
      });
    });

    it("allows confirmation when only warnings exist", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          valid: true,
          currentState: "todo",
          toState: "wip",
          guardFailures: [],
          guardWarnings: [
            { guard: "session_scope", message: "Warning" },
          ],
        }),
      });

      render(<TaskTransitionDialog {...defaultProps} />);

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /confirm/i }),
        ).not.toBeDisabled();
      });
    });
  });

  describe("confirmation", () => {
    it("calls transition API with confirmed=true on confirm", async () => {
      const user = userEvent.setup();

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            allowed: true,
            from: "todo",
            to: "wip",
            guardFailures: [],
            guardWarnings: [],
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            success: true,
            taskId: "T001",
            fromState: "todo",
            toState: "wip",
          }),
        });

      render(<TaskTransitionDialog {...defaultProps} />);

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /confirm/i }),
        ).not.toBeDisabled();
      });

      await user.click(screen.getByRole("button", { name: /confirm/i }));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining("/api/v1/projects/project-1/tasks/T001/transition"),
          expect.objectContaining({
            method: "POST",
            body: JSON.stringify({ toState: "wip", confirmed: true }),
          }),
        );
      });
    });

    it("calls onSuccess callback after successful transition", async () => {
      const user = userEvent.setup();
      const onSuccess = vi.fn();

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            allowed: true,
            from: "todo",
            to: "wip",
            guardFailures: [],
            guardWarnings: [],
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            success: true,
            taskId: "T001",
            fromState: "todo",
            toState: "wip",
          }),
        });

      render(<TaskTransitionDialog {...defaultProps} onSuccess={onSuccess} />);

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /confirm/i }),
        ).not.toBeDisabled();
      });

      await user.click(screen.getByRole("button", { name: /confirm/i }));

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalledWith({
          success: true,
          taskId: "T001",
          fromState: "todo",
          toState: "wip",
        });
      });
    });

    it("shows loading state during confirmation", async () => {
      const user = userEvent.setup();

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            allowed: true,
            from: "todo",
            to: "wip",
            guardFailures: [],
            guardWarnings: [],
          }),
        })
        .mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<TaskTransitionDialog {...defaultProps} />);

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /confirm/i }),
        ).not.toBeDisabled();
      });

      await user.click(screen.getByRole("button", { name: /confirm/i }));

      await waitFor(() => {
        expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
      });
    });
  });

  describe("cancellation", () => {
    it("calls onClose when cancel button is clicked", async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          valid: true,
          currentState: "todo",
          toState: "wip",
          guardFailures: [],
          guardWarnings: [],
        }),
      });

      render(<TaskTransitionDialog {...defaultProps} onClose={onClose} />);

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /cancel/i }),
        ).toBeInTheDocument();
      });

      await user.click(screen.getByRole("button", { name: /cancel/i }));
      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });

  describe("error handling", () => {
    it("displays error when preview fetch fails", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
      });

      render(<TaskTransitionDialog {...defaultProps} />);

      await waitFor(() => {
        expect(
          screen.getByText(/Failed to fetch preview/i),
        ).toBeInTheDocument();
      });
    });

    it("displays error when transition fails", async () => {
      const user = userEvent.setup();

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            allowed: true,
            from: "todo",
            to: "wip",
            guardFailures: [],
            guardWarnings: [],
          }),
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({
            error: "Transition not allowed",
          }),
        });

      render(<TaskTransitionDialog {...defaultProps} />);

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /confirm/i }),
        ).not.toBeDisabled();
      });

      await user.click(screen.getByRole("button", { name: /confirm/i }));

      await waitFor(() => {
        expect(
          screen.getByText(/Transition not allowed/i),
        ).toBeInTheDocument();
      });
    });
  });

  describe("accessibility", () => {
    it("has accessible dialog role", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          valid: true,
          currentState: "todo",
          toState: "wip",
          guardFailures: [],
          guardWarnings: [],
        }),
      });

      render(<TaskTransitionDialog {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByRole("dialog")).toBeInTheDocument();
      });
    });
  });
});
