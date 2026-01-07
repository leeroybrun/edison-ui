import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AuditEventList } from "./AuditEventList";
import type { AuditEvent } from "./types";

const mockAuditEvents: AuditEvent[] = [
  {
    ts: "2025-12-27T10:00:00Z",
    event: "cli.invocation.end",
    invocationId: "inv-123",
    sessionId: "session-1",
    taskId: null,
    command: "edison task transition T005 --to done",
    exitCode: 0,
    durationMs: 1234,
    projectRoot: null,
    pid: null,
  },
  {
    ts: "2025-12-27T09:30:00Z",
    event: "cli.invocation.start",
    invocationId: "inv-122",
    sessionId: "session-1",
    taskId: null,
    command: "edison session start",
    exitCode: 0,
    durationMs: 567,
    projectRoot: null,
    pid: null,
  },
  {
    ts: "2025-12-27T09:00:00Z",
    event: "cli.invocation.end",
    invocationId: "inv-121",
    sessionId: null,
    taskId: null,
    command: "edison task create",
    exitCode: 1,
    durationMs: 2000,
    projectRoot: null,
    pid: null,
  },
];

describe("AuditEventList", () => {
  it("renders audit event items", () => {
    render(
      <AuditEventList
        items={mockAuditEvents}
        loading={false}
        hasMore={false}
        onLoadMore={() => {}}
        showRaw={false}
      />,
    );

    // cli.invocation.end appears twice in mock data
    expect(screen.getAllByText("cli.invocation.end")).toHaveLength(2);
    expect(screen.getByText("cli.invocation.start")).toBeInTheDocument();
  });

  it("displays command text for each event", () => {
    render(
      <AuditEventList
        items={mockAuditEvents}
        loading={false}
        hasMore={false}
        onLoadMore={() => {}}
        showRaw={false}
      />,
    );

    expect(screen.getByText(/edison task transition/)).toBeInTheDocument();
    expect(screen.getByText(/edison session start/)).toBeInTheDocument();
    expect(screen.getByText(/edison task create/)).toBeInTheDocument();
  });

  it("shows exit code badges with appropriate colors", () => {
    render(
      <AuditEventList
        items={mockAuditEvents}
        loading={false}
        hasMore={false}
        onLoadMore={() => {}}
        showRaw={false}
      />,
    );

    // Exit code 0 should have success styling
    const successBadges = screen.getAllByText("0");
    expect(successBadges.length).toBeGreaterThan(0);

    // Exit code 1 should have error styling
    expect(screen.getByText("1")).toBeInTheDocument();
  });

  it("displays duration in human-readable format", () => {
    render(
      <AuditEventList
        items={mockAuditEvents}
        loading={false}
        hasMore={false}
        onLoadMore={() => {}}
        showRaw={false}
      />,
    );

    // 1234ms should be shown as "1.2s" or similar
    expect(screen.getByText(/1\.2s|1234ms/)).toBeInTheDocument();
  });

  it("shows loading state", () => {
    render(
      <AuditEventList
        items={[]}
        loading={true}
        hasMore={false}
        onLoadMore={() => {}}
        showRaw={false}
      />,
    );

    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("shows Load more button when hasMore is true", () => {
    render(
      <AuditEventList
        items={mockAuditEvents}
        loading={false}
        hasMore={true}
        onLoadMore={() => {}}
        showRaw={false}
      />,
    );

    expect(
      screen.getByRole("button", { name: /load more/i }),
    ).toBeInTheDocument();
  });

  it("hides Load more button when hasMore is false", () => {
    render(
      <AuditEventList
        items={mockAuditEvents}
        loading={false}
        hasMore={false}
        onLoadMore={() => {}}
        showRaw={false}
      />,
    );

    expect(
      screen.queryByRole("button", { name: /load more/i }),
    ).not.toBeInTheDocument();
  });

  it("calls onLoadMore when Load more button is clicked", () => {
    const onLoadMore = vi.fn();
    render(
      <AuditEventList
        items={mockAuditEvents}
        loading={false}
        hasMore={true}
        onLoadMore={onLoadMore}
        showRaw={false}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /load more/i }));
    expect(onLoadMore).toHaveBeenCalledTimes(1);
  });

  it("displays empty state when no items", () => {
    render(
      <AuditEventList
        items={[]}
        loading={false}
        hasMore={false}
        onLoadMore={() => {}}
        showRaw={false}
      />,
    );

    expect(screen.getByText(/no audit events/i)).toBeInTheDocument();
  });

  it("shows collapsible event details when showRaw is true", () => {
    render(
      <AuditEventList
        items={mockAuditEvents}
        loading={false}
        hasMore={false}
        onLoadMore={() => {}}
        showRaw={true}
      />,
    );

    // In raw mode, should show invocation IDs
    expect(screen.getByText(/inv-123/)).toBeInTheDocument();
  });

  it("allows expanding individual event details", () => {
    render(
      <AuditEventList
        items={mockAuditEvents}
        loading={false}
        hasMore={false}
        onLoadMore={() => {}}
        showRaw={false}
      />,
    );

    // Find expand buttons and click first one
    const expandButtons = screen.getAllByRole("button", {
      name: /details|expand/i,
    });
    expect(expandButtons.length).toBeGreaterThan(0);

    fireEvent.click(expandButtons[0]);

    // After expanding, should show invocation ID
    expect(screen.getByText(/inv-123/)).toBeInTheDocument();
  });

  it("has accessible list structure", () => {
    render(
      <AuditEventList
        items={mockAuditEvents}
        loading={false}
        hasMore={false}
        onLoadMore={() => {}}
        showRaw={false}
      />,
    );

    expect(screen.getByRole("list")).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(3);
  });

  it("shows session ID when available", () => {
    render(
      <AuditEventList
        items={mockAuditEvents}
        loading={false}
        hasMore={false}
        onLoadMore={() => {}}
        showRaw={false}
      />,
    );

    // session-1 appears in 2 events
    expect(screen.getAllByText("session-1")).toHaveLength(2);
  });
});
