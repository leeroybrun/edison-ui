import { render, screen } from "@testing-library/react";

import { NavSidebar } from "./NavSidebar";

describe("NavSidebar", () => {
  it("renders navigation with sidebar role", () => {
    render(<NavSidebar />);
    expect(screen.getByRole("navigation")).toBeInTheDocument();
  });

  it("renders Dashboard link pointing to home", () => {
    render(<NavSidebar />);
    const dashboardLink = screen.getByRole("link", { name: /dashboard/i });
    expect(dashboardLink).toBeInTheDocument();
    expect(dashboardLink).toHaveAttribute("href", "/");
  });

  it("renders Projects link pointing to /projects", () => {
    render(<NavSidebar />);
    const projectsLink = screen.getByRole("link", { name: /projects/i });
    expect(projectsLink).toBeInTheDocument();
    expect(projectsLink).toHaveAttribute("href", "/projects");
  });

  it("renders Settings link pointing to /settings", () => {
    render(<NavSidebar />);
    const settingsLink = screen.getByRole("link", { name: /settings/i });
    expect(settingsLink).toBeInTheDocument();
    expect(settingsLink).toHaveAttribute("href", "/settings");
  });

  it("renders app title in the top bar area", () => {
    render(<NavSidebar />);
    expect(screen.getByText("Edison UI")).toBeInTheDocument();
  });

  it("has accessible navigation landmark", () => {
    render(<NavSidebar />);
    const nav = screen.getByRole("navigation");
    expect(nav).toHaveAttribute("aria-label", "Main navigation");
  });
});
