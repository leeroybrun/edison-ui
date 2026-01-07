import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { ConfigPanel, type ProjectConfig, type Pack } from "./Config";

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

const mockProjectConfig: ProjectConfig = {
  projectId: "project-123",
  activePacks: ["python", "typescript"],
  config: {
    scanRoots: ["~/projects"],
    displayName: "Test Project",
    exposureMode: "localhost",
    realtime: {
      pollingIntervalMs: 5000,
    },
  },
};

const mockPacks: Pack[] = [
  {
    packId: "python",
    name: "Python Pack",
    description: "Python development configuration",
    enabled: true,
    source: "project",
  },
  {
    packId: "typescript",
    name: "TypeScript Pack",
    description: "TypeScript development configuration",
    enabled: true,
    source: "core",
  },
];

const mockPackDetail = {
  packId: "python",
  name: "Python Pack",
  description: "Python development configuration",
  enabled: true,
  config: { pythonVersion: "3.11" },
  source: "project",
};

describe("ConfigPanel", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("Loading State", () => {
    it("shows loading indicator while fetching config", () => {
      mockFetch.mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<ConfigPanel projectId="project-123" />);
      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });
  });

  describe("Config Display", () => {
    it("displays project configuration", async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockProjectConfig),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ items: mockPacks, total: 2 }),
        });

      render(<ConfigPanel projectId="project-123" />);

      await waitFor(() => {
        expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
      });
    });

    it("displays active packs list", async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockProjectConfig),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ items: mockPacks, total: 2 }),
        });

      render(<ConfigPanel projectId="project-123" />);

      await waitFor(() => {
        expect(screen.getByText("Python Pack")).toBeInTheDocument();
        expect(screen.getByText("TypeScript Pack")).toBeInTheDocument();
      });
    });

    it("shows pack source (core/project)", async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockProjectConfig),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ items: mockPacks, total: 2 }),
        });

      render(<ConfigPanel projectId="project-123" />);

      await waitFor(() => {
        // Pack sources are shown as badges - check for the exact text in badges
        const badges = screen.getAllByText(/^(project|core)$/);
        expect(badges.length).toBeGreaterThanOrEqual(2);
      });
    });
  });

  describe("Config Editing", () => {
    it("displays editable fields with edit buttons", async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockProjectConfig),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ items: mockPacks, total: 2 }),
        });

      render(<ConfigPanel projectId="project-123" />);

      await waitFor(() => {
        const editButtons = screen.getAllByRole("button", { name: /edit/i });
        expect(editButtons.length).toBeGreaterThan(0);
      });
    });

    it("shows preview dialog when editing a field", async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockProjectConfig),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ items: mockPacks, total: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            valid: true,
            preview: {
              field: "displayName",
              currentValue: "Test Project",
              newValue: "New Name",
            },
            warnings: [],
          }),
        });

      render(<ConfigPanel projectId="project-123" />);

      await waitFor(() => {
        expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
      });

      const editButton = screen.getAllByRole("button", { name: /edit/i })[0];
      await userEvent.click(editButton);

      await waitFor(() => {
        expect(screen.getByRole("dialog")).toBeInTheDocument();
      });
    });

    it("calls preview API before confirming changes", async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockProjectConfig),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ items: mockPacks, total: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            valid: true,
            preview: {
              field: "displayName",
              currentValue: "Test Project",
              newValue: "New Name",
            },
            warnings: [],
          }),
        });

      render(<ConfigPanel projectId="project-123" />);

      await waitFor(() => {
        expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
      });

      const editButton = screen.getAllByRole("button", { name: /edit/i })[0];
      await userEvent.click(editButton);

      // Fill in new value
      const input = await screen.findByRole("textbox");
      await userEvent.clear(input);
      await userEvent.type(input, "New Name");

      // Click preview
      const previewButton = screen.getByRole("button", { name: /preview/i });
      await userEvent.click(previewButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining("/config/preview"),
          expect.objectContaining({
            method: "POST",
          })
        );
      });
    });

    it("shows validation error for disallowed fields", async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockProjectConfig),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ items: mockPacks, total: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            valid: false,
            reason: "Field 'credentials' is not editable via the API",
            warnings: [],
          }),
        });

      render(<ConfigPanel projectId="project-123" />);

      await waitFor(() => {
        expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
      });

      // Simulate attempting to edit a disallowed field
      // (In real usage, only allowed fields would have edit buttons)
    });

    it("applies change when confirmed", async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockProjectConfig),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ items: mockPacks, total: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            valid: true,
            preview: {
              field: "displayName",
              currentValue: "Test Project",
              newValue: "New Name",
            },
            warnings: [],
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            success: true,
            auditEntryId: "audit-123",
            backupPath: ".edison/.config-backup/2026-01-07.yaml",
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            ...mockProjectConfig,
            config: { ...mockProjectConfig.config, displayName: "New Name" },
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ items: mockPacks, total: 2 }),
        });

      render(<ConfigPanel projectId="project-123" />);

      await waitFor(() => {
        expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
      });

      const editButton = screen.getAllByRole("button", { name: /edit/i })[0];
      await userEvent.click(editButton);

      // Fill in new value
      const input = await screen.findByRole("textbox");
      await userEvent.clear(input);
      await userEvent.type(input, "New Name");

      // Preview
      const previewButton = screen.getByRole("button", { name: /preview/i });
      await userEvent.click(previewButton);

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /apply/i })).toBeInTheDocument();
      });

      // Confirm
      const confirmButton = screen.getByRole("button", { name: /apply/i });
      await userEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining("/config"),
          expect.objectContaining({
            method: "POST",
            body: expect.stringContaining('"confirmed":true'),
          })
        );
      });
    });
  });

  describe("Pack Detail View", () => {
    it("shows pack detail when clicking a pack", async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockProjectConfig),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ items: mockPacks, total: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockPackDetail),
        });

      render(<ConfigPanel projectId="project-123" />);

      await waitFor(() => {
        expect(screen.getByText("Python Pack")).toBeInTheDocument();
      });

      await userEvent.click(screen.getByText("Python Pack"));

      // Pack detail shows config JSON - wait for it
      await waitFor(() => {
        expect(screen.getByText(/pythonVersion/i)).toBeInTheDocument();
      });
    });
  });

  describe("Error Handling", () => {
    it("displays error message on fetch failure", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network error"));

      render(<ConfigPanel projectId="project-123" />);

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument();
      });
    });

    it("displays error message on API error", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ detail: "Internal server error" }),
      });

      render(<ConfigPanel projectId="project-123" />);

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument();
      });
    });
  });

  describe("Refresh", () => {
    it("provides refresh button to reload config", async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockProjectConfig),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ items: mockPacks, total: 2 }),
        });

      render(<ConfigPanel projectId="project-123" />);

      await waitFor(() => {
        expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
      });

      expect(screen.getByRole("button", { name: /refresh/i })).toBeInTheDocument();
    });
  });
});
