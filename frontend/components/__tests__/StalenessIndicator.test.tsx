/**
 * TDD Tests for StalenessIndicator Component (T053).
 *
 * RED PHASE: Tests written before implementation.
 * Expected: All tests should fail initially.
 *
 * Tests cover:
 * - Shows last update time
 * - Visual indicator for staleness level
 * - Manual refresh button
 * - Accessibility requirements
 */
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

describe("StalenessIndicator", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  describe("rendering", () => {
    it("should render with fresh state", async () => {
      const { StalenessIndicator } = await import("../StalenessIndicator");

      const now = Date.now();
      vi.setSystemTime(now);

      render(
        <StalenessIndicator
          lastUpdatedAt={new Date(now - 2000)}
          onRefresh={() => {}}
        />,
      );

      expect(screen.getByText(/just now|2s ago/i)).toBeInTheDocument();
    });

    it("should render with stale state", async () => {
      const { StalenessIndicator } = await import("../StalenessIndicator");

      const now = Date.now();
      vi.setSystemTime(now);

      render(
        <StalenessIndicator
          lastUpdatedAt={new Date(now - 15000)}
          onRefresh={() => {}}
        />,
      );

      expect(screen.getByText(/15s ago/i)).toBeInTheDocument();
    });

    it("should render with very stale state", async () => {
      const { StalenessIndicator } = await import("../StalenessIndicator");

      const now = Date.now();
      vi.setSystemTime(now);

      render(
        <StalenessIndicator
          lastUpdatedAt={new Date(now - 60000)}
          onRefresh={() => {}}
        />,
      );

      expect(screen.getByText(/1m ago/i)).toBeInTheDocument();
    });

    it("should render loading state when refreshing", async () => {
      const { StalenessIndicator } = await import("../StalenessIndicator");

      const now = Date.now();
      vi.setSystemTime(now);

      render(
        <StalenessIndicator
          isRefreshing={true}
          lastUpdatedAt={new Date(now)}
          onRefresh={() => {}}
        />,
      );

      expect(screen.getByLabelText(/refreshing/i)).toBeInTheDocument();
    });

    it("should render without last update time when null", async () => {
      const { StalenessIndicator } = await import("../StalenessIndicator");

      render(<StalenessIndicator lastUpdatedAt={null} onRefresh={() => {}} />);

      expect(screen.getByText(/never updated/i)).toBeInTheDocument();
    });
  });

  describe("visual indicators", () => {
    it("should show green indicator for fresh data", async () => {
      const { StalenessIndicator } = await import("../StalenessIndicator");

      const now = Date.now();
      vi.setSystemTime(now);

      render(
        <StalenessIndicator
          lastUpdatedAt={new Date(now - 2000)}
          onRefresh={() => {}}
        />,
      );

      const indicator = screen.getByTestId("staleness-indicator");
      expect(indicator).toHaveClass("bg-green-500");
    });

    it("should show yellow indicator for stale data", async () => {
      const { StalenessIndicator } = await import("../StalenessIndicator");

      const now = Date.now();
      vi.setSystemTime(now);

      render(
        <StalenessIndicator
          lastUpdatedAt={new Date(now - 15000)}
          onRefresh={() => {}}
        />,
      );

      const indicator = screen.getByTestId("staleness-indicator");
      expect(indicator).toHaveClass("bg-yellow-500");
    });

    it("should show red indicator for very stale data", async () => {
      const { StalenessIndicator } = await import("../StalenessIndicator");

      const now = Date.now();
      vi.setSystemTime(now);

      render(
        <StalenessIndicator
          lastUpdatedAt={new Date(now - 60000)}
          onRefresh={() => {}}
        />,
      );

      const indicator = screen.getByTestId("staleness-indicator");
      expect(indicator).toHaveClass("bg-red-500");
    });

    it("should show gray indicator when never updated", async () => {
      const { StalenessIndicator } = await import("../StalenessIndicator");

      render(<StalenessIndicator lastUpdatedAt={null} onRefresh={() => {}} />);

      const indicator = screen.getByTestId("staleness-indicator");
      expect(indicator).toHaveClass("bg-gray-400");
    });
  });

  describe("refresh button", () => {
    it("should render refresh button", async () => {
      const { StalenessIndicator } = await import("../StalenessIndicator");

      render(
        <StalenessIndicator lastUpdatedAt={new Date()} onRefresh={() => {}} />,
      );

      expect(
        screen.getByRole("button", { name: /refresh/i }),
      ).toBeInTheDocument();
    });

    it("should call onRefresh when button clicked", async () => {
      const { StalenessIndicator } = await import("../StalenessIndicator");
      const onRefresh = vi.fn();

      render(
        <StalenessIndicator lastUpdatedAt={new Date()} onRefresh={onRefresh} />,
      );

      fireEvent.click(screen.getByRole("button", { name: /refresh/i }));

      expect(onRefresh).toHaveBeenCalledTimes(1);
    });

    it("should disable refresh button while refreshing", async () => {
      const { StalenessIndicator } = await import("../StalenessIndicator");

      render(
        <StalenessIndicator
          isRefreshing={true}
          lastUpdatedAt={new Date()}
          onRefresh={() => {}}
        />,
      );

      expect(screen.getByRole("button", { name: /refresh/i })).toBeDisabled();
    });

    it("should show spinner in button while refreshing", async () => {
      const { StalenessIndicator } = await import("../StalenessIndicator");

      render(
        <StalenessIndicator
          isRefreshing={true}
          lastUpdatedAt={new Date()}
          onRefresh={() => {}}
        />,
      );

      expect(screen.getByTestId("refresh-spinner")).toBeInTheDocument();
    });
  });

  describe("connection state", () => {
    it("should show connected state", async () => {
      const { StalenessIndicator } = await import("../StalenessIndicator");

      render(
        <StalenessIndicator
          connectionState="connected"
          lastUpdatedAt={new Date()}
          onRefresh={() => {}}
        />,
      );

      expect(screen.getByText(/connected/i)).toBeInTheDocument();
    });

    it("should show connecting state", async () => {
      const { StalenessIndicator } = await import("../StalenessIndicator");

      render(
        <StalenessIndicator
          connectionState="connecting"
          lastUpdatedAt={new Date()}
          onRefresh={() => {}}
        />,
      );

      expect(screen.getByText(/connecting/i)).toBeInTheDocument();
    });

    it("should show disconnected state", async () => {
      const { StalenessIndicator } = await import("../StalenessIndicator");

      render(
        <StalenessIndicator
          connectionState="disconnected"
          lastUpdatedAt={new Date()}
          onRefresh={() => {}}
        />,
      );

      expect(screen.getByText(/disconnected/i)).toBeInTheDocument();
    });

    it("should show polling state", async () => {
      const { StalenessIndicator } = await import("../StalenessIndicator");

      render(
        <StalenessIndicator
          connectionState="polling"
          lastUpdatedAt={new Date()}
          onRefresh={() => {}}
        />,
      );

      expect(screen.getByText(/polling/i)).toBeInTheDocument();
    });
  });

  describe("accessibility", () => {
    it("should have accessible label for staleness indicator", async () => {
      const { StalenessIndicator } = await import("../StalenessIndicator");

      const now = Date.now();
      vi.setSystemTime(now);

      render(
        <StalenessIndicator
          lastUpdatedAt={new Date(now - 15000)}
          onRefresh={() => {}}
        />,
      );

      const indicator = screen.getByTestId("staleness-indicator");
      expect(indicator).toHaveAttribute("aria-label");
    });

    it("should have accessible refresh button", async () => {
      const { StalenessIndicator } = await import("../StalenessIndicator");

      render(
        <StalenessIndicator lastUpdatedAt={new Date()} onRefresh={() => {}} />,
      );

      const button = screen.getByRole("button", { name: /refresh/i });
      expect(button).toHaveAccessibleName();
    });

    it("should announce status changes to screen readers", async () => {
      const { StalenessIndicator } = await import("../StalenessIndicator");

      render(
        <StalenessIndicator
          connectionState="disconnected"
          lastUpdatedAt={new Date()}
          onRefresh={() => {}}
        />,
      );

      const status = screen.getByRole("status");
      expect(status).toBeInTheDocument();
    });
  });

  describe("compact mode", () => {
    it("should render in compact mode", async () => {
      const { StalenessIndicator } = await import("../StalenessIndicator");

      render(
        <StalenessIndicator
          compact={true}
          lastUpdatedAt={new Date()}
          onRefresh={() => {}}
        />,
      );

      const container = screen.getByTestId("staleness-container");
      expect(container).toHaveClass("compact");
    });

    it("should hide connection text in compact mode", async () => {
      const { StalenessIndicator } = await import("../StalenessIndicator");

      render(
        <StalenessIndicator
          compact={true}
          connectionState="connected"
          lastUpdatedAt={new Date()}
          onRefresh={() => {}}
        />,
      );

      expect(screen.queryByText(/connected/i)).not.toBeInTheDocument();
    });
  });

  describe("auto update", () => {
    it("should update displayed time automatically", async () => {
      const { StalenessIndicator } = await import("../StalenessIndicator");

      const now = Date.now();
      vi.setSystemTime(now);

      const { rerender } = render(
        <StalenessIndicator
          lastUpdatedAt={new Date(now)}
          onRefresh={() => {}}
        />,
      );

      expect(screen.getByText(/just now/i)).toBeInTheDocument();

      // Advance time by 10 seconds
      vi.setSystemTime(now + 10000);
      await vi.advanceTimersByTimeAsync(1000); // Trigger update

      // Re-render to pick up time change
      rerender(
        <StalenessIndicator
          lastUpdatedAt={new Date(now)}
          onRefresh={() => {}}
        />,
      );

      expect(screen.getByText(/1[01]s ago/i)).toBeInTheDocument();
    });
  });
});
