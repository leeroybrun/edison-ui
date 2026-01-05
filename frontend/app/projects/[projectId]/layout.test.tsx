import { render, screen, within } from "@testing-library/react";

import ProjectLayout from "./layout";

// Mock useParams, usePathname, useRouter to provide navigation context
vi.mock("next/navigation", () => ({
  useParams: () => ({ projectId: "test-project-123" }),
  usePathname: () => "/projects/test-project-123/tasks",
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
  }),
}));

describe("ProjectLayout", () => {
  describe("structure", () => {
    it("renders the project sidebar", () => {
      render(
        <ProjectLayout>
          <div>Test content</div>
        </ProjectLayout>,
      );

      // Should have navigation landmark from sidebar
      expect(
        screen.getByRole("navigation", { name: "Project navigation" }),
      ).toBeInTheDocument();
    });

    it("renders children in the main content area", () => {
      render(
        <ProjectLayout>
          <div data-testid="page-content">Page Content</div>
        </ProjectLayout>,
      );

      expect(screen.getByTestId("page-content")).toBeInTheDocument();
      expect(screen.getByText("Page Content")).toBeInTheDocument();
    });

    it("has an accessible main content landmark", () => {
      render(
        <ProjectLayout>
          <div>Content</div>
        </ProjectLayout>,
      );

      expect(screen.getByRole("main")).toBeInTheDocument();
    });
  });

  describe("desktop navigation items", () => {
    // Test within the sidebar navigation specifically
    it("renders Dashboard link with correct href in sidebar", () => {
      render(
        <ProjectLayout>
          <div>Content</div>
        </ProjectLayout>,
      );

      const sidebarNav = screen.getByRole("navigation", {
        name: "Project navigation",
      });
      const link = within(sidebarNav).getByRole("link", { name: "Dashboard" });
      expect(link).toHaveAttribute("href", "/projects/test-project-123");
    });

    it("renders Sessions link with correct href in sidebar", () => {
      render(
        <ProjectLayout>
          <div>Content</div>
        </ProjectLayout>,
      );

      const sidebarNav = screen.getByRole("navigation", {
        name: "Project navigation",
      });
      const link = within(sidebarNav).getByRole("link", { name: "Sessions" });
      expect(link).toHaveAttribute(
        "href",
        "/projects/test-project-123/sessions",
      );
    });

    it("renders Tasks link with correct href in sidebar", () => {
      render(
        <ProjectLayout>
          <div>Content</div>
        </ProjectLayout>,
      );

      const sidebarNav = screen.getByRole("navigation", {
        name: "Project navigation",
      });
      const link = within(sidebarNav).getByRole("link", { name: "Tasks" });
      expect(link).toHaveAttribute("href", "/projects/test-project-123/tasks");
    });

    it("renders QA link with correct href in sidebar", () => {
      render(
        <ProjectLayout>
          <div>Content</div>
        </ProjectLayout>,
      );

      const sidebarNav = screen.getByRole("navigation", {
        name: "Project navigation",
      });
      const link = within(sidebarNav).getByRole("link", { name: "QA" });
      expect(link).toHaveAttribute("href", "/projects/test-project-123/qa");
    });

    it("renders Agents link with correct href in sidebar", () => {
      render(
        <ProjectLayout>
          <div>Content</div>
        </ProjectLayout>,
      );

      const sidebarNav = screen.getByRole("navigation", {
        name: "Project navigation",
      });
      const link = within(sidebarNav).getByRole("link", { name: "Agents" });
      expect(link).toHaveAttribute("href", "/projects/test-project-123/agents");
    });

    it("renders Settings link with correct href in sidebar", () => {
      render(
        <ProjectLayout>
          <div>Content</div>
        </ProjectLayout>,
      );

      const sidebarNav = screen.getByRole("navigation", {
        name: "Project navigation",
      });
      const link = within(sidebarNav).getByRole("link", { name: "Settings" });
      expect(link).toHaveAttribute(
        "href",
        "/projects/test-project-123/settings",
      );
    });
  });

  describe("back navigation", () => {
    it("includes back links to projects list in both desktop and mobile", () => {
      render(
        <ProjectLayout>
          <div>Content</div>
        </ProjectLayout>,
      );

      // Should have back links in both views
      const backLinks = screen.getAllByRole("link", {
        name: /back to projects/i,
      });
      expect(backLinks.length).toBeGreaterThanOrEqual(1);

      // All back links should point to the home page
      backLinks.forEach((link) => {
        expect(link).toHaveAttribute("href", "/");
      });
    });
  });

  describe("active state detection", () => {
    it("marks the current route as active based on pathname", () => {
      render(
        <ProjectLayout>
          <div>Content</div>
        </ProjectLayout>,
      );

      // Based on our mock, pathname is /projects/test-project-123/tasks
      // Check within sidebar navigation
      const sidebarNav = screen.getByRole("navigation", {
        name: "Project navigation",
      });
      const tasksLink = within(sidebarNav).getByRole("link", { name: "Tasks" });
      expect(tasksLink).toHaveAttribute("aria-current", "page");
    });

    it("marks Tasks as active in mobile navigation", () => {
      render(
        <ProjectLayout>
          <div>Content</div>
        </ProjectLayout>,
      );

      const mobileNav = screen.getByRole("navigation", {
        name: "Mobile project navigation",
      });
      const tasksLink = within(mobileNav).getByRole("link", { name: "Tasks" });
      expect(tasksLink).toHaveAttribute("aria-current", "page");
    });
  });

  describe("responsive layout", () => {
    it("renders sidebar with data-testid for responsive testing", () => {
      render(
        <ProjectLayout>
          <div>Content</div>
        </ProjectLayout>,
      );

      expect(screen.getByTestId("project-sidebar")).toBeInTheDocument();
    });
  });

  describe("mobile navigation", () => {
    it("renders mobile navigation header on small screens", () => {
      render(
        <ProjectLayout>
          <div>Content</div>
        </ProjectLayout>,
      );

      // Mobile nav should be present in DOM (hidden via CSS on desktop)
      const mobileNav = screen.getByRole("navigation", {
        name: "Mobile project navigation",
      });
      expect(mobileNav).toBeInTheDocument();
    });

    it("renders all navigation items in mobile navigation", () => {
      render(
        <ProjectLayout>
          <div>Content</div>
        </ProjectLayout>,
      );

      const mobileNav = screen.getByRole("navigation", {
        name: "Mobile project navigation",
      });

      // Verify all links are present in mobile nav
      expect(
        within(mobileNav).getByRole("link", { name: "Dashboard" }),
      ).toBeInTheDocument();
      expect(
        within(mobileNav).getByRole("link", { name: "Sessions" }),
      ).toBeInTheDocument();
      expect(
        within(mobileNav).getByRole("link", { name: "Tasks" }),
      ).toBeInTheDocument();
      expect(
        within(mobileNav).getByRole("link", { name: "QA" }),
      ).toBeInTheDocument();
      expect(
        within(mobileNav).getByRole("link", { name: "Agents" }),
      ).toBeInTheDocument();
      expect(
        within(mobileNav).getByRole("link", { name: "Settings" }),
      ).toBeInTheDocument();
    });
  });
});
