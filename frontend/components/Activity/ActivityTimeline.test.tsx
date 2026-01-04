import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ActivityTimeline } from "./ActivityTimeline";
import type { ActivityItem } from "./types";

const mockActivityItems: ActivityItem[] = [
  {
    timestamp: "2025-12-27T10:00:00Z",
    eventType: "task.transition",
    summary: "Task T005 moved to done",
    sessionId: "session-1",
    taskId: "T005",
    invocationId: "inv-123",
    actor: {
      osUser: "leeroy",
      displayName: "Leeroy Jenkins",
    },
  },
  {
    timestamp: "2025-12-27T09:30:00Z",
    eventType: "session.start",
    summary: "Session started",
    sessionId: "session-1",
    taskId: null,
    invocationId: "inv-122",
    actor: {
      osUser: "leeroy",
      displayName: "Leeroy Jenkins",
    },
  },
  {
    timestamp: "2025-12-27T09:00:00Z",
    eventType: "task.create",
    summary: "Task T005 created",
    sessionId: null,
    taskId: "T005",
    invocationId: "inv-121",
    actor: {
      osUser: "system",
      displayName: "System",
    },
  },
];

describe("ActivityTimeline", () => {
  it("renders activity items with timestamps", () => {
    render(
      <ActivityTimeline
        items={mockActivityItems}
        loading={false}
        hasMore={false}
        onLoadMore={() => {}}
      />
    );

    expect(screen.getByText("Task T005 moved to done")).toBeInTheDocument();
    expect(screen.getByText("Session started")).toBeInTheDocument();
    expect(screen.getByText("Task T005 created")).toBeInTheDocument();
  });

  it("displays actor information for each item", () => {
    render(
      <ActivityTimeline
        items={mockActivityItems}
        loading={false}
        hasMore={false}
        onLoadMore={() => {}}
      />
    );

    expect(screen.getAllByText("Leeroy Jenkins")).toHaveLength(2);
    expect(screen.getByText("System")).toBeInTheDocument();
  });

  it("shows event type badges", () => {
    render(
      <ActivityTimeline
        items={mockActivityItems}
        loading={false}
        hasMore={false}
        onLoadMore={() => {}}
      />
    );

    expect(screen.getByText("task.transition")).toBeInTheDocument();
    expect(screen.getByText("session.start")).toBeInTheDocument();
    expect(screen.getByText("task.create")).toBeInTheDocument();
  });

  it("displays loading state", () => {
    render(
      <ActivityTimeline
        items={[]}
        loading={true}
        hasMore={false}
        onLoadMore={() => {}}
      />
    );

    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("shows Load more button when hasMore is true", () => {
    render(
      <ActivityTimeline
        items={mockActivityItems}
        loading={false}
        hasMore={true}
        onLoadMore={() => {}}
      />
    );

    expect(screen.getByRole("button", { name: /load more/i })).toBeInTheDocument();
  });

  it("hides Load more button when hasMore is false", () => {
    render(
      <ActivityTimeline
        items={mockActivityItems}
        loading={false}
        hasMore={false}
        onLoadMore={() => {}}
      />
    );

    expect(screen.queryByRole("button", { name: /load more/i })).not.toBeInTheDocument();
  });

  it("calls onLoadMore when Load more button is clicked", () => {
    const onLoadMore = vi.fn();
    render(
      <ActivityTimeline
        items={mockActivityItems}
        loading={false}
        hasMore={true}
        onLoadMore={onLoadMore}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: /load more/i }));
    expect(onLoadMore).toHaveBeenCalledTimes(1);
  });

  it("displays empty state when no items", () => {
    render(
      <ActivityTimeline
        items={[]}
        loading={false}
        hasMore={false}
        onLoadMore={() => {}}
      />
    );

    expect(screen.getByText(/no activity/i)).toBeInTheDocument();
  });

  it("formats timestamps in human-readable format", () => {
    const { container } = render(
      <ActivityTimeline
        items={mockActivityItems}
        loading={false}
        hasMore={false}
        onLoadMore={() => {}}
      />
    );

    // Should display formatted timestamps (time elements with datetime)
    const timeElements = container.querySelectorAll("time");
    expect(timeElements).toHaveLength(3);
    expect(timeElements[0]).toHaveAttribute("dateTime", "2025-12-27T10:00:00Z");
  });

  it("has accessible timeline structure", () => {
    render(
      <ActivityTimeline
        items={mockActivityItems}
        loading={false}
        hasMore={false}
        onLoadMore={() => {}}
      />
    );

    // Timeline should use semantic list structure
    expect(screen.getByRole("list")).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(3);
  });

  it("shows session and task links when available", () => {
    render(
      <ActivityTimeline
        items={mockActivityItems}
        loading={false}
        hasMore={false}
        onLoadMore={() => {}}
      />
    );

    // session-1 appears in 2 items (first and second)
    expect(screen.getAllByText("session-1")).toHaveLength(2);
    // T005 appears in 2 items (first and third)
    expect(screen.getAllByText("T005")).toHaveLength(2);
  });

  it("button is focusable for keyboard navigation", () => {
    const onLoadMore = vi.fn();
    render(
      <ActivityTimeline
        items={mockActivityItems}
        loading={false}
        hasMore={true}
        onLoadMore={onLoadMore}
      />
    );

    const button = screen.getByRole("button", { name: /load more/i });
    // Button should be focusable (native buttons handle Enter/Space automatically)
    expect(button).not.toHaveAttribute("tabIndex", "-1");
    expect(button).toHaveAttribute("type", "button");
  });
});
