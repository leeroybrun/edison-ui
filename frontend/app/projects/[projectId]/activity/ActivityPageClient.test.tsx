import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useRouter, useSearchParams } from "next/navigation";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { ActivityPageClient } from "./ActivityPageClient";

vi.mock("next/navigation", () => ({
  useRouter: vi.fn(),
  useSearchParams: vi.fn(),
}));

describe("ActivityPageClient", () => {
  const mockPush = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useRouter as ReturnType<typeof vi.fn>).mockReturnValue({ push: mockPush });
    (useSearchParams as ReturnType<typeof vi.fn>).mockReturnValue(
      new URLSearchParams(),
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  function renderSubject() {
    return render(
      <ActivityPageClient
        hasMore={false}
        initialActivityItems={[]}
        initialAuditItems={[]}
        initialFilters={{}}
        initialView="activity"
        projectId="proj-1"
        sessions={[]}
        tasks={[]}
      />,
    );
  }

  it("shows a client-side error alert when a fetch fails", async () => {
    global.fetch = vi.fn().mockRejectedValueOnce(new Error("boom"));

    renderSubject();

    const user = userEvent.setup();
    await act(async () => {
      await user.click(screen.getByRole("button", { name: "Raw Audit" }));
    });

    await waitFor(() => {
      expect(screen.getByText("Failed to load")).toBeInTheDocument();
    });
  });
});
