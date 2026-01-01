import { render, screen } from "@testing-library/react";

import Loading from "./loading";

describe("Loading", () => {
  it("renders loading state", () => {
    render(<Loading />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("has accessible loading text for screen readers", () => {
    render(<Loading />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("displays a visual loading indicator", () => {
    render(<Loading />);
    // The loading indicator should have some visual element
    const status = screen.getByRole("status");
    expect(status).toBeInTheDocument();
  });
});
