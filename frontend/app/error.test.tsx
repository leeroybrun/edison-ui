import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import ErrorPage from "./error";

describe("ErrorPage", () => {
  const mockReset = vi.fn();
  const mockError = { message: "Something went wrong" } as Error & {
    digest?: string;
  };

  beforeEach(() => {
    mockReset.mockClear();
  });

  it("renders error alert with accessible role", () => {
    render(<ErrorPage error={mockError} reset={mockReset} />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("displays error message", () => {
    render(<ErrorPage error={mockError} reset={mockReset} />);
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
  });

  it("renders a retry button", () => {
    render(<ErrorPage error={mockError} reset={mockReset} />);
    expect(
      screen.getByRole("button", { name: /try again|retry/i })
    ).toBeInTheDocument();
  });

  it("calls reset when retry button is clicked", async () => {
    const user = userEvent.setup();
    render(<ErrorPage error={mockError} reset={mockReset} />);

    const retryButton = screen.getByRole("button", { name: /try again|retry/i });
    await user.click(retryButton);

    expect(mockReset).toHaveBeenCalledTimes(1);
  });

  it("has accessible error heading", () => {
    render(<ErrorPage error={mockError} reset={mockReset} />);
    expect(
      screen.getByRole("heading", { name: /error/i })
    ).toBeInTheDocument();
  });
});
