import { render, screen } from "@testing-library/react";

import NotFound from "./not-found";

describe("NotFound", () => {
  it("renders 404 status", () => {
    render(<NotFound />);
    expect(screen.getByText(/404/i)).toBeInTheDocument();
  });

  it("displays page not found message", () => {
    render(<NotFound />);
    expect(screen.getByText(/page not found|not found/i)).toBeInTheDocument();
  });

  it("renders link back to dashboard", () => {
    render(<NotFound />);
    const homeLink = screen.getByRole("link", { name: /dashboard|home|go back/i });
    expect(homeLink).toBeInTheDocument();
    expect(homeLink).toHaveAttribute("href", "/");
  });

  it("has accessible heading", () => {
    render(<NotFound />);
    expect(screen.getByRole("heading")).toBeInTheDocument();
  });
});
