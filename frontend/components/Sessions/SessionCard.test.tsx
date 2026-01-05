import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SessionCard } from "./SessionCard";
import type { Session } from "./types";

const mockSession: Session = {
  sessionId: "happy-pid-12345",
  state: "active",
  phase: "implementation",
  owner: "alice",
  taskCount: 5,
  createdAt: "2025-12-27T10:00:00Z",
  lastActiveAt: "2025-12-28T15:30:00Z",
  git: {
    branchName: "feature/new-ui",
    baseBranch: "main",
  },
};

describe("SessionCard", () => {
  it("renders session ID", () => {
    render(<SessionCard projectId="my-project" session={mockSession} />);

    expect(screen.getByText("happy-pid-12345")).toBeInTheDocument();
  });

  it("renders state badge with correct styling for active state", () => {
    render(<SessionCard projectId="my-project" session={mockSession} />);

    const badge = screen.getByText("active");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("bg-blue-100");
  });

  it("renders state badge with correct styling for paused state", () => {
    const pausedSession: Session = { ...mockSession, state: "paused" };
    render(<SessionCard projectId="my-project" session={pausedSession} />);

    const badge = screen.getByText("paused");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("bg-yellow-100");
  });

  it("renders state badge with correct styling for completed state", () => {
    const completedSession: Session = { ...mockSession, state: "completed" };
    render(<SessionCard projectId="my-project" session={completedSession} />);

    const badge = screen.getByText("completed");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("bg-green-100");
  });

  it("renders state badge with correct styling for draft state", () => {
    const draftSession: Session = { ...mockSession, state: "draft" };
    render(<SessionCard projectId="my-project" session={draftSession} />);

    const badge = screen.getByText("draft");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("bg-gray-100");
  });

  it("renders state badge with correct styling for abandoned state", () => {
    const abandonedSession: Session = { ...mockSession, state: "abandoned" };
    render(<SessionCard projectId="my-project" session={abandonedSession} />);

    const badge = screen.getByText("abandoned");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("bg-red-100");
  });

  it("displays task count", () => {
    render(<SessionCard projectId="my-project" session={mockSession} />);

    expect(screen.getByText("5 tasks")).toBeInTheDocument();
  });

  it("displays last active time", () => {
    render(<SessionCard projectId="my-project" session={mockSession} />);

    // Should show relative or formatted time
    expect(screen.getByText(/last active/i)).toBeInTheDocument();
  });

  it("displays branch name", () => {
    render(<SessionCard projectId="my-project" session={mockSession} />);

    expect(screen.getByText("feature/new-ui")).toBeInTheDocument();
  });

  it("calls onClick when clicked", () => {
    const handleClick = vi.fn();
    render(
      <SessionCard
        onClick={handleClick}
        projectId="my-project"
        session={mockSession}
      />,
    );

    const card = screen.getByRole("article");
    fireEvent.click(card);

    expect(handleClick).toHaveBeenCalledWith("happy-pid-12345");
  });

  it("shows selected state when isSelected is true", () => {
    render(
      <SessionCard isSelected projectId="my-project" session={mockSession} />,
    );

    const card = screen.getByRole("article");
    expect(card).toHaveClass("ring-2");
  });

  it("is keyboard accessible", () => {
    const handleClick = vi.fn();
    render(
      <SessionCard
        onClick={handleClick}
        projectId="my-project"
        session={mockSession}
      />,
    );

    const card = screen.getByRole("article");
    fireEvent.keyDown(card, { key: "Enter" });

    expect(handleClick).toHaveBeenCalledWith("happy-pid-12345");
  });

  it("displays phase information", () => {
    render(<SessionCard projectId="my-project" session={mockSession} />);

    expect(screen.getByText("implementation")).toBeInTheDocument();
  });
});
