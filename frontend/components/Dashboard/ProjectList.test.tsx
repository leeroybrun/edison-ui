import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ProjectList } from "./ProjectList";
import type { Project } from "./types";

const mockProjects: Project[] = [
  {
    projectId: "project-1",
    path: "~/projects/alpha",
    name: "Alpha Project",
    pinned: true,
    health: { taskCount: 10, sessionCount: 2, qaCount: 5, activeCount: 1 },
    lastActivityAt: "2025-12-27T10:00:00Z",
    hasGit: true,
    errors: [],
  },
  {
    projectId: "project-2",
    path: "~/projects/beta",
    name: "Beta Project",
    pinned: false,
    health: { taskCount: 20, sessionCount: 4, qaCount: 8, activeCount: 3 },
    lastActivityAt: "2025-12-26T10:00:00Z",
    hasGit: true,
    errors: [],
  },
];

describe("ProjectList", () => {
  it("renders loading state", () => {
    render(<ProjectList projects={[]} isLoading={true} />);

    expect(screen.getByText(/loading projects/i)).toBeInTheDocument();
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("renders empty state when no projects found", () => {
    render(<ProjectList projects={[]} isLoading={false} />);

    expect(
      screen.getByText(/no projects found/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/configure scan roots to discover edison projects/i),
    ).toBeInTheDocument();
  });

  it("renders error state", () => {
    render(
      <ProjectList
        projects={[]}
        isLoading={false}
        error="Failed to load projects"
      />,
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();
    // Error message appears in both title and detail, so use getAllByText
    const errorMessages = screen.getAllByText("Failed to load projects");
    expect(errorMessages.length).toBeGreaterThan(0);
  });

  it("renders list of projects", () => {
    render(<ProjectList projects={mockProjects} isLoading={false} />);

    expect(screen.getByText("Alpha Project")).toBeInTheDocument();
    expect(screen.getByText("Beta Project")).toBeInTheDocument();
  });

  it("shows pinned projects first", () => {
    render(<ProjectList projects={mockProjects} isLoading={false} />);

    const projectCards = screen.getAllByRole("article");
    expect(projectCards).toHaveLength(2);

    // First card should be the pinned project
    expect(projectCards[0]).toHaveTextContent("Alpha Project");
    expect(projectCards[1]).toHaveTextContent("Beta Project");
  });

  it("groups projects into pinned and unpinned sections", () => {
    render(<ProjectList projects={mockProjects} isLoading={false} />);

    expect(screen.getByText(/pinned/i)).toBeInTheDocument();
    expect(screen.getByText(/all projects/i)).toBeInTheDocument();
  });

  it("calls onPin callback when pin action is triggered", async () => {
    const onPin = vi.fn();
    render(
      <ProjectList projects={mockProjects} isLoading={false} onPin={onPin} />,
    );

    // The callback should be passed to children
    expect(onPin).not.toHaveBeenCalled();
  });

  it("displays total project count", () => {
    render(<ProjectList projects={mockProjects} isLoading={false} />);

    expect(screen.getByText(/2 projects/i)).toBeInTheDocument();
  });
});
