import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { SearchDialog, type SearchResult, type SearchResponse } from "./Search";

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

const mockSearchResponse: SearchResponse = {
  query: "auth",
  results: {
    tasks: [
      {
        taskId: "T001",
        title: "Implement authentication",
        snippet: "Add user auth with JWT tokens",
        score: 0.95,
        projectId: "project-1",
      },
    ],
    sessions: [
      {
        sessionId: "session-1",
        snippet: "Working on auth flow",
        score: 0.8,
        projectId: "project-1",
      },
    ],
    qa: [],
    memory: [],
  },
  totalHits: 2,
};

describe("SearchDialog", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("Visibility", () => {
    it("is hidden when isOpen is false", () => {
      render(<SearchDialog isOpen={false} onClose={vi.fn()} />);
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    it("renders as a dialog when isOpen is true", () => {
      render(<SearchDialog isOpen={true} onClose={vi.fn()} />);
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
  });

  describe("Search Input", () => {
    it("renders search input with placeholder", () => {
      render(<SearchDialog isOpen={true} onClose={vi.fn()} />);
      expect(screen.getByPlaceholderText(/search tasks/i)).toBeInTheDocument();
    });

    it("focuses search input on open", async () => {
      render(<SearchDialog isOpen={true} onClose={vi.fn()} />);
      const input = screen.getByPlaceholderText(/search tasks/i);
      await waitFor(() => {
        expect(document.activeElement).toBe(input);
      });
    });

    it("clears input when dialog closes and reopens", async () => {
      const { rerender } = render(<SearchDialog isOpen={true} onClose={vi.fn()} />);

      const input = screen.getByPlaceholderText(/search tasks/i);
      await userEvent.type(input, "test query");

      rerender(<SearchDialog isOpen={false} onClose={vi.fn()} />);
      rerender(<SearchDialog isOpen={true} onClose={vi.fn()} />);

      expect(screen.getByPlaceholderText(/search tasks/i)).toHaveValue("");
    });
  });

  describe("Search Behavior", () => {
    it("calls search API after debounce delay", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockSearchResponse),
      });

      render(<SearchDialog isOpen={true} onClose={vi.fn()} />);
      const input = screen.getByPlaceholderText(/search tasks/i);

      await userEvent.type(input, "auth");

      // Wait for debounce and API call
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled();
      }, { timeout: 500 });
    });

    it("displays results after successful search", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockSearchResponse),
      });

      render(<SearchDialog isOpen={true} onClose={vi.fn()} />);
      const input = screen.getByPlaceholderText(/search tasks/i);

      await userEvent.type(input, "auth");

      await waitFor(() => {
        expect(screen.getByText("Implement authentication")).toBeInTheDocument();
      });
    });

    it("displays 'No results found' for empty results", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          query: "xyz",
          results: { tasks: [], sessions: [], qa: [], memory: [] },
          totalHits: 0,
        }),
      });

      render(<SearchDialog isOpen={true} onClose={vi.fn()} />);
      const input = screen.getByPlaceholderText(/search tasks/i);

      await userEvent.type(input, "xyz");

      await waitFor(() => {
        expect(screen.getByText(/no results found/i)).toBeInTheDocument();
      });
    });

    it("shows loading indicator while searching", async () => {
      mockFetch.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve(mockSearchResponse),
        }), 200))
      );

      render(<SearchDialog isOpen={true} onClose={vi.fn()} />);
      const input = screen.getByPlaceholderText(/search tasks/i);

      await userEvent.type(input, "auth");

      await waitFor(() => {
        expect(screen.getByText(/searching/i)).toBeInTheDocument();
      });
    });
  });

  describe("Keyboard Navigation", () => {
    it("closes on Escape key", async () => {
      const onClose = vi.fn();
      render(<SearchDialog isOpen={true} onClose={onClose} />);

      fireEvent.keyDown(screen.getByPlaceholderText(/search tasks/i), { key: "Escape" });

      expect(onClose).toHaveBeenCalled();
    });

    it("navigates results with arrow keys", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockSearchResponse),
      });

      render(<SearchDialog isOpen={true} onClose={vi.fn()} />);
      const input = screen.getByPlaceholderText(/search tasks/i);

      await userEvent.type(input, "auth");

      await waitFor(() => {
        expect(screen.getByText("Implement authentication")).toBeInTheDocument();
      });

      fireEvent.keyDown(input, { key: "ArrowDown" });

      // Check first result is selected
      const firstResult = screen.getByText("Implement authentication").closest("li");
      expect(firstResult).toHaveAttribute("aria-selected", "true");
    });
  });

  describe("Project-scoped search", () => {
    it("uses project-scoped endpoint when projectId provided", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockSearchResponse),
      });

      render(
        <SearchDialog
          isOpen={true}
          onClose={vi.fn()}
          projectId="project-123"
        />
      );
      const input = screen.getByPlaceholderText(/search tasks/i);

      await userEvent.type(input, "auth");

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining("/projects/project-123/search"),
          expect.any(Object)
        );
      });
    });

    it("uses global search endpoint when no projectId", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockSearchResponse),
      });

      render(<SearchDialog isOpen={true} onClose={vi.fn()} />);
      const input = screen.getByPlaceholderText(/search tasks/i);

      await userEvent.type(input, "auth");

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining("/search?"),
          expect.any(Object)
        );
      });
    });
  });

  describe("Scope Filter", () => {
    it("renders scope filter dropdown", () => {
      render(<SearchDialog isOpen={true} onClose={vi.fn()} />);
      expect(screen.getByLabelText(/scope/i)).toBeInTheDocument();
    });

    it("filters by selected scope", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockSearchResponse),
      });

      render(<SearchDialog isOpen={true} onClose={vi.fn()} />);

      // Select tasks scope
      const scopeSelect = screen.getByLabelText(/scope/i);
      await userEvent.selectOptions(scopeSelect, "tasks");

      const input = screen.getByPlaceholderText(/search tasks/i);
      await userEvent.type(input, "auth");

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining("scope=tasks"),
          expect.any(Object)
        );
      });
    });
  });

  describe("Result Selection", () => {
    it("calls onSelect with result when clicked", async () => {
      const onSelect = vi.fn();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockSearchResponse),
      });

      render(
        <SearchDialog
          isOpen={true}
          onClose={vi.fn()}
          onSelect={onSelect}
        />
      );
      const input = screen.getByPlaceholderText(/search tasks/i);

      await userEvent.type(input, "auth");

      await waitFor(() => {
        expect(screen.getByText("Implement authentication")).toBeInTheDocument();
      });

      await userEvent.click(screen.getByText("Implement authentication"));

      expect(onSelect).toHaveBeenCalledWith(
        expect.objectContaining({
          taskId: "T001",
          title: "Implement authentication",
        })
      );
    });

    it("calls onSelect and closes dialog on Enter", async () => {
      const onClose = vi.fn();
      const onSelect = vi.fn();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockSearchResponse),
      });

      render(
        <SearchDialog
          isOpen={true}
          onClose={onClose}
          onSelect={onSelect}
        />
      );
      const input = screen.getByPlaceholderText(/search tasks/i);

      await userEvent.type(input, "auth");

      await waitFor(() => {
        expect(screen.getByText("Implement authentication")).toBeInTheDocument();
      });

      // Select first result
      fireEvent.keyDown(input, { key: "ArrowDown" });
      fireEvent.keyDown(input, { key: "Enter" });

      expect(onSelect).toHaveBeenCalled();
      expect(onClose).toHaveBeenCalled();
    });
  });

  describe("Accessibility", () => {
    it("has proper ARIA attributes for combobox pattern", () => {
      render(<SearchDialog isOpen={true} onClose={vi.fn()} />);

      const input = screen.getByPlaceholderText(/search tasks/i);
      expect(input).toHaveAttribute("aria-autocomplete", "list");
      expect(input).toHaveAttribute("aria-expanded");
      expect(input).toHaveAttribute("aria-controls");
    });

    it("announces search results to screen readers", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockSearchResponse),
      });

      render(<SearchDialog isOpen={true} onClose={vi.fn()} />);
      const input = screen.getByPlaceholderText(/search tasks/i);

      await userEvent.type(input, "auth");

      await waitFor(() => {
        expect(screen.getByRole("listbox")).toBeInTheDocument();
      });
    });
  });

  describe("Backdrop", () => {
    it("closes dialog when backdrop is clicked", async () => {
      const onClose = vi.fn();
      render(<SearchDialog isOpen={true} onClose={onClose} />);

      const backdrop = screen.getByTestId("search-backdrop");
      await userEvent.click(backdrop);

      expect(onClose).toHaveBeenCalled();
    });
  });
});
