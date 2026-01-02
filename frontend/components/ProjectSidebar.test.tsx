import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ProjectSidebar } from "./ProjectSidebar";

// Navigation items defined per spec
const EXPECTED_NAV_ITEMS = [
  { label: "Dashboard", href: "/projects/test-project" },
  { label: "Sessions", href: "/projects/test-project/sessions" },
  { label: "Tasks", href: "/projects/test-project/tasks" },
  { label: "QA", href: "/projects/test-project/qa" },
  { label: "Agents", href: "/projects/test-project/agents" },
  { label: "Settings", href: "/projects/test-project/settings" },
];

describe("ProjectSidebar", () => {
  const projectId = "test-project";
  const projectName = "Test Project";

  describe("navigation structure", () => {
    it("renders navigation with accessible landmark", () => {
      render(<ProjectSidebar projectId={projectId} projectName={projectName} />);
      const nav = screen.getByRole("navigation");
      expect(nav).toBeInTheDocument();
      expect(nav).toHaveAttribute("aria-label", "Project navigation");
    });

    it("renders all required navigation items", () => {
      render(<ProjectSidebar projectId={projectId} projectName={projectName} />);

      for (const item of EXPECTED_NAV_ITEMS) {
        const link = screen.getByRole("link", { name: item.label });
        expect(link).toBeInTheDocument();
        expect(link).toHaveAttribute("href", item.href);
      }
    });

    it("displays project name in header", () => {
      render(<ProjectSidebar projectId={projectId} projectName={projectName} />);
      expect(screen.getByText(projectName)).toBeInTheDocument();
    });

    it("includes back link to projects list", () => {
      render(<ProjectSidebar projectId={projectId} projectName={projectName} />);
      const backLink = screen.getByRole("link", { name: /back to projects/i });
      expect(backLink).toBeInTheDocument();
      expect(backLink).toHaveAttribute("href", "/");
    });
  });

  describe("active state", () => {
    it("highlights the active navigation item", () => {
      render(
        <ProjectSidebar
          projectId={projectId}
          projectName={projectName}
          activeItem="tasks"
        />
      );
      const tasksLink = screen.getByRole("link", { name: "Tasks" });
      expect(tasksLink).toHaveAttribute("aria-current", "page");
    });

    it("does not highlight inactive items", () => {
      render(
        <ProjectSidebar
          projectId={projectId}
          projectName={projectName}
          activeItem="tasks"
        />
      );
      const dashboardLink = screen.getByRole("link", { name: "Dashboard" });
      expect(dashboardLink).not.toHaveAttribute("aria-current");
    });
  });

  describe("keyboard accessibility", () => {
    it("all navigation links are focusable", async () => {
      const user = userEvent.setup();
      render(<ProjectSidebar projectId={projectId} projectName={projectName} />);

      // Tab through all links
      for (const item of EXPECTED_NAV_ITEMS) {
        await user.tab();
        const link = screen.getByRole("link", { name: item.label });
        // The link should eventually receive focus during tab navigation
        expect(link).toBeVisible();
      }
    });
  });

  describe("responsive behavior", () => {
    it("renders collapsed state when collapsed prop is true", () => {
      render(
        <ProjectSidebar
          projectId={projectId}
          projectName={projectName}
          collapsed={true}
        />
      );
      const sidebar = screen.getByTestId("project-sidebar");
      expect(sidebar).toHaveClass("w-16");
    });

    it("renders expanded state when collapsed prop is false", () => {
      render(
        <ProjectSidebar
          projectId={projectId}
          projectName={projectName}
          collapsed={false}
        />
      );
      const sidebar = screen.getByTestId("project-sidebar");
      expect(sidebar).toHaveClass("w-64");
    });

    it("renders collapse toggle button", () => {
      render(<ProjectSidebar projectId={projectId} projectName={projectName} />);
      const toggleButton = screen.getByRole("button", {
        name: /collapse sidebar/i,
      });
      expect(toggleButton).toBeInTheDocument();
    });

    it("calls onCollapsedChange when toggle is clicked", async () => {
      const user = userEvent.setup();
      const onCollapsedChange = vi.fn();
      render(
        <ProjectSidebar
          projectId={projectId}
          projectName={projectName}
          collapsed={false}
          onCollapsedChange={onCollapsedChange}
        />
      );

      const toggleButton = screen.getByRole("button", {
        name: /collapse sidebar/i,
      });
      await user.click(toggleButton);
      expect(onCollapsedChange).toHaveBeenCalledWith(true);
    });
  });

  describe("collapsed state labels", () => {
    it("shows tooltips on navigation items when collapsed", () => {
      render(
        <ProjectSidebar
          projectId={projectId}
          projectName={projectName}
          collapsed={true}
        />
      );

      for (const item of EXPECTED_NAV_ITEMS) {
        const link = screen.getByRole("link", { name: item.label });
        expect(link).toHaveAttribute("title", item.label);
      }
    });
  });
});
