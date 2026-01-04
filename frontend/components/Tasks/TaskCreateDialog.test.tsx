import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { TaskCreateDialog } from "./TaskCreateDialog";

// Mock fetch for API calls
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe("TaskCreateDialog", () => {
  const defaultProps = {
    projectId: "project-1",
    sessionId: null as string | null,
    parentId: null as string | null,
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

  describe("rendering", () => {
    it("renders nothing when open is false", () => {
      const { container } = render(
        <TaskCreateDialog {...defaultProps} open={false} />,
      );
      expect(container.querySelector("[role='dialog']")).toBeNull();
    });

    it("renders dialog when open is true", () => {
      render(<TaskCreateDialog {...defaultProps} />);
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    it("displays create task title", () => {
      render(<TaskCreateDialog {...defaultProps} />);
      expect(screen.getByText(/create.*task/i)).toBeInTheDocument();
    });

    it("shows title input field", () => {
      render(<TaskCreateDialog {...defaultProps} />);
      expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
    });
  });

  describe("form input", () => {
    it("allows entering task title", async () => {
      const user = userEvent.setup();
      render(<TaskCreateDialog {...defaultProps} />);

      const input = screen.getByLabelText(/title/i);
      await user.type(input, "New Task Title");

      expect(input).toHaveValue("New Task Title");
    });

    it("disables preview button when title is empty", () => {
      render(<TaskCreateDialog {...defaultProps} />);
      expect(screen.getByRole("button", { name: /preview/i })).toBeDisabled();
    });

    it("enables preview button when title is entered", async () => {
      const user = userEvent.setup();
      render(<TaskCreateDialog {...defaultProps} />);

      const input = screen.getByLabelText(/title/i);
      await user.type(input, "New Task");

      expect(
        screen.getByRole("button", { name: /preview/i }),
      ).not.toBeDisabled();
    });
  });

  describe("preview", () => {
    it("fetches preview when title is entered and form submitted", async () => {
      const user = userEvent.setup();

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          valid: true,
          guardFailures: [],
          guardWarnings: [],
          preview: { taskId: "T099", title: "New Task", description: "", state: "todo" },
        }),
      });

      render(<TaskCreateDialog {...defaultProps} />);

      const input = screen.getByLabelText(/title/i);
      await user.type(input, "New Task");
      await user.click(screen.getByRole("button", { name: /preview/i }));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining("/api/v1/projects/project-1/tasks/preview"),
          expect.objectContaining({
            method: "POST",
            body: expect.stringContaining("New Task"),
          }),
        );
      });
    });

    it("displays preview with task ID after fetching", async () => {
      const user = userEvent.setup();

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          valid: true,
          guardFailures: [],
          guardWarnings: [],
          preview: { taskId: "T099", title: "New Task", description: "", state: "todo" },
        }),
      });

      render(<TaskCreateDialog {...defaultProps} />);

      const input = screen.getByLabelText(/title/i);
      await user.type(input, "New Task");
      await user.click(screen.getByRole("button", { name: /preview/i }));

      await waitFor(() => {
        expect(screen.getByText(/T099/)).toBeInTheDocument();
      });
    });

    it("includes sessionId in preview request when provided", async () => {
      const user = userEvent.setup();

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          valid: true,
          guardFailures: [],
          guardWarnings: [],
          preview: { taskId: "T099", title: "New Task", description: "", state: "todo" },
        }),
      });

      render(<TaskCreateDialog {...defaultProps} sessionId="session-1" />);

      const input = screen.getByLabelText(/title/i);
      await user.type(input, "New Task");
      await user.click(screen.getByRole("button", { name: /preview/i }));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.any(String),
          expect.objectContaining({
            body: expect.stringContaining("session-1"),
          }),
        );
      });
    });

    it("includes parentId in preview request when provided", async () => {
      const user = userEvent.setup();

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          valid: true,
          guardFailures: [],
          guardWarnings: [],
          preview: { taskId: "T099", title: "New Task", description: "", state: "todo" },
        }),
      });

      render(<TaskCreateDialog {...defaultProps} parentId="T001" />);

      const input = screen.getByLabelText(/title/i);
      await user.type(input, "New Task");
      await user.click(screen.getByRole("button", { name: /preview/i }));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.any(String),
          expect.objectContaining({
            body: expect.stringContaining("T001"),
          }),
        );
      });
    });
  });

  describe("guard failures", () => {
    it("displays guard failures from preview", async () => {
      const user = userEvent.setup();

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          valid: false,
          guardFailures: [
            { guard: "session_required", reason: "No active session" },
          ],
          guardWarnings: [],
          preview: { taskId: "T099", title: "New Task", description: "", state: "todo" },
        }),
      });

      render(<TaskCreateDialog {...defaultProps} />);

      const input = screen.getByLabelText(/title/i);
      await user.type(input, "New Task");
      await user.click(screen.getByRole("button", { name: /preview/i }));

      await waitFor(() => {
        expect(screen.getByText("No active session")).toBeInTheDocument();
      });
    });

    it("disables create button when there are guard failures", async () => {
      const user = userEvent.setup();

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          valid: false,
          guardFailures: [
            { guard: "session_required", reason: "No active session" },
          ],
          guardWarnings: [],
          preview: { taskId: "T099", title: "New Task", description: "", state: "todo" },
        }),
      });

      render(<TaskCreateDialog {...defaultProps} />);

      const input = screen.getByLabelText(/title/i);
      await user.type(input, "New Task");
      await user.click(screen.getByRole("button", { name: /preview/i }));

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /create/i })).toBeDisabled();
      });
    });
  });

  describe("creation", () => {
    it("calls create API when confirm is clicked", async () => {
      const user = userEvent.setup();

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            valid: true,
            guardFailures: [],
            guardWarnings: [],
            preview: { taskId: "T099", title: "New Task", description: "", state: "todo" },
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            success: true,
            taskId: "T099",
            title: "New Task",
            state: "todo",
          }),
        });

      render(<TaskCreateDialog {...defaultProps} />);

      const input = screen.getByLabelText(/title/i);
      await user.type(input, "New Task");
      await user.click(screen.getByRole("button", { name: /preview/i }));

      await waitFor(() => {
        expect(screen.getByText(/T099/)).toBeInTheDocument();
      });

      await user.click(screen.getByRole("button", { name: /create/i }));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining("/api/v1/projects/project-1/tasks"),
          expect.objectContaining({
            method: "POST",
            body: expect.stringContaining("confirmed"),
          }),
        );
      });
    });

    it("calls onSuccess after successful creation", async () => {
      const user = userEvent.setup();
      const onSuccess = vi.fn();

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            valid: true,
            guardFailures: [],
            guardWarnings: [],
            preview: { taskId: "T099", title: "New Task", description: "", state: "todo" },
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            success: true,
            taskId: "T099",
            title: "New Task",
            state: "todo",
          }),
        });

      render(<TaskCreateDialog {...defaultProps} onSuccess={onSuccess} />);

      const input = screen.getByLabelText(/title/i);
      await user.type(input, "New Task");
      await user.click(screen.getByRole("button", { name: /preview/i }));

      await waitFor(() => {
        expect(screen.getByText(/T099/)).toBeInTheDocument();
      });

      await user.click(screen.getByRole("button", { name: /create/i }));

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalledWith({
          success: true,
          taskId: "T099",
          title: "New Task",
          state: "todo",
        });
      });
    });
  });

  describe("cancellation", () => {
    it("calls onClose when cancel is clicked", async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();

      render(<TaskCreateDialog {...defaultProps} onClose={onClose} />);

      await user.click(screen.getByRole("button", { name: /cancel/i }));
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it("resets form when dialog closes and reopens", async () => {
      const user = userEvent.setup();
      const { rerender } = render(<TaskCreateDialog {...defaultProps} />);

      const input = screen.getByLabelText(/title/i);
      await user.type(input, "Some Title");
      expect(input).toHaveValue("Some Title");

      // Close dialog
      rerender(<TaskCreateDialog {...defaultProps} open={false} />);

      // Reopen dialog
      rerender(<TaskCreateDialog {...defaultProps} open={true} />);

      const newInput = screen.getByLabelText(/title/i);
      expect(newInput).toHaveValue("");
    });
  });

  describe("loading state", () => {
    it("shows loading during preview fetch", async () => {
      const user = userEvent.setup();

      mockFetch.mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<TaskCreateDialog {...defaultProps} />);

      const input = screen.getByLabelText(/title/i);
      await user.type(input, "New Task");
      await user.click(screen.getByRole("button", { name: /preview/i }));

      await waitFor(() => {
        expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
      });
    });

    it("shows loading during creation", async () => {
      const user = userEvent.setup();

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            valid: true,
            guardFailures: [],
            guardWarnings: [],
            preview: { taskId: "T099", title: "New Task", description: "", state: "todo" },
          }),
        })
        .mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<TaskCreateDialog {...defaultProps} />);

      const input = screen.getByLabelText(/title/i);
      await user.type(input, "New Task");
      await user.click(screen.getByRole("button", { name: /preview/i }));

      await waitFor(() => {
        expect(screen.getByText(/T099/)).toBeInTheDocument();
      });

      await user.click(screen.getByRole("button", { name: /create/i }));

      await waitFor(() => {
        expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
      });
    });
  });

  describe("error handling", () => {
    it("displays error when preview fails", async () => {
      const user = userEvent.setup();

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
      });

      render(<TaskCreateDialog {...defaultProps} />);

      const input = screen.getByLabelText(/title/i);
      await user.type(input, "New Task");
      await user.click(screen.getByRole("button", { name: /preview/i }));

      await waitFor(() => {
        expect(screen.getByText(/failed to/i)).toBeInTheDocument();
      });
    });

    it("displays error when creation fails", async () => {
      const user = userEvent.setup();

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            valid: true,
            guardFailures: [],
            guardWarnings: [],
            preview: { taskId: "T099", title: "New Task", description: "", state: "todo" },
          }),
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({
            error: "Creation failed",
          }),
        });

      render(<TaskCreateDialog {...defaultProps} />);

      const input = screen.getByLabelText(/title/i);
      await user.type(input, "New Task");
      await user.click(screen.getByRole("button", { name: /preview/i }));

      await waitFor(() => {
        expect(screen.getByText(/T099/)).toBeInTheDocument();
      });

      await user.click(screen.getByRole("button", { name: /create/i }));

      await waitFor(() => {
        expect(screen.getByText(/Creation failed/i)).toBeInTheDocument();
      });
    });
  });

  describe("accessibility", () => {
    it("has accessible dialog role", () => {
      render(<TaskCreateDialog {...defaultProps} />);
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    it("has labeled input field", () => {
      render(<TaskCreateDialog {...defaultProps} />);
      const input = screen.getByLabelText(/title/i);
      expect(input).toBeInTheDocument();
      expect(input).toHaveAccessibleName();
    });
  });
});
