import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ProjectCard } from "./ProjectCard";
import type { Project } from "./types";

const mockProject: Project = {
  projectId: "test-project-1",
  path: "~/projects/test",
  name: "Test Project",
  pinned: false,
  health: {
    taskCount: 42,
    sessionCount: 3,
    qaCount: 15,
    activeCount: 2,
  },
  lastActivityAt: "2025-12-27T10:00:00Z",
  hasGit: true,
  errors: [],
};

describe("ProjectCard", () => {
  it("renders project name and path", () => {
    render(<ProjectCard project={mockProject} />);

    expect(screen.getByText("Test Project")).toBeInTheDocument();
    expect(screen.getByText("~/projects/test")).toBeInTheDocument();
  });

  it("renders health counts", () => {
    render(<ProjectCard project={mockProject} />);

    expect(screen.getByText("42")).toBeInTheDocument(); // tasks
    expect(screen.getByText("3")).toBeInTheDocument(); // sessions
    expect(screen.getByText("15")).toBeInTheDocument(); // qa
    expect(screen.getByText("2")).toBeInTheDocument(); // active
  });

  it("renders git indicator when hasGit is true", () => {
    render(<ProjectCard project={mockProject} />);

    expect(screen.getByLabelText("Git repository")).toBeInTheDocument();
  });

  it("does not render git indicator when hasGit is false", () => {
    const projectWithoutGit = { ...mockProject, hasGit: false };
    render(<ProjectCard project={projectWithoutGit} />);

    expect(screen.queryByLabelText("Git repository")).not.toBeInTheDocument();
  });

  it("renders pinned state correctly", () => {
    const pinnedProject = { ...mockProject, pinned: true };
    render(<ProjectCard project={pinnedProject} />);

    const pinButton = screen.getByRole("button", { name: /unpin/i });
    expect(pinButton).toBeInTheDocument();
  });

  it("renders unpinned state correctly", () => {
    render(<ProjectCard project={mockProject} />);

    const pinButton = screen.getByRole("button", { name: /pin project/i });
    expect(pinButton).toBeInTheDocument();
  });

  it("calls onPin when pin button is clicked", async () => {
    const user = userEvent.setup();
    const onPin = vi.fn();
    render(<ProjectCard project={mockProject} onPin={onPin} />);

    const pinButton = screen.getByRole("button", { name: /pin project/i });
    await user.click(pinButton);

    expect(onPin).toHaveBeenCalledWith("test-project-1", true);
  });

  it("calls onPin with false when unpin button is clicked", async () => {
    const user = userEvent.setup();
    const onPin = vi.fn();
    const pinnedProject = { ...mockProject, pinned: true };
    render(<ProjectCard project={pinnedProject} onPin={onPin} />);

    const pinButton = screen.getByRole("button", { name: /unpin/i });
    await user.click(pinButton);

    expect(onPin).toHaveBeenCalledWith("test-project-1", false);
  });

  it("renders last activity time in relative format", () => {
    render(<ProjectCard project={mockProject} />);

    // Should show some relative time indicator
    expect(screen.getByText(/last activity/i)).toBeInTheDocument();
  });

  it("renders error badge when project has errors", () => {
    const projectWithErrors = {
      ...mockProject,
      errors: ["Missing .project directory"],
    };
    render(<ProjectCard project={projectWithErrors} />);

    expect(screen.getByText("1 error")).toBeInTheDocument();
  });

  it("links to project detail page", () => {
    render(<ProjectCard project={mockProject} />);

    const link = screen.getByRole("link", { name: /view project/i });
    expect(link).toHaveAttribute("href", "/projects/test-project-1");
  });
});
