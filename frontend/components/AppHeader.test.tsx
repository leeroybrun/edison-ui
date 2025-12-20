import { render, screen } from "@testing-library/react";

import { AppHeader } from "./AppHeader";

describe("AppHeader", () => {
  it("renders app name and projects link", () => {
    render(<AppHeader />);
    expect(screen.getByRole("link", { name: "Edison UI" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Projects" })).toBeInTheDocument();
  });
});

