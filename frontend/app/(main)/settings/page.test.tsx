import { beforeEach, describe, expect, test, vi, type Mock } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import SettingsPage from "./page";

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock PairingWizard
vi.mock("../../../components/Pairing", () => ({
  PairingWizard: ({
    open,
    onClose,
    onPaired,
  }: {
    open: boolean;
    onClose: () => void;
    onPaired: (result: { token: string; expiresAt: string }) => void;
  }) =>
    open ? (
      <div data-testid="pairing-wizard">
        <button onClick={onClose}>Close Wizard</button>
        <button
          onClick={() =>
            onPaired({ token: "test-token", expiresAt: "2026-01-05" })
          }
        >
          Complete Pairing
        </button>
      </div>
    ) : null,
}));

describe("SettingsPage", () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  function mockSettingsResponse(exposureMode: string) {
    return {
      ok: true,
      json: async () => ({
        scanRoots: ["/Users/test/Projects"],
        exposureMode,
        realtime: {
          enabled: true,
          watcherEnabled: true,
          pollingIntervalMs: 1000,
        },
        actor: {
          osUser: "testuser",
          displayName: "Test User",
        },
      }),
    };
  }

  function mockTailscaleStatusResponse(running = false) {
    return {
      ok: true,
      json: async () => ({
        installed: running,
        running,
        hostname: running ? "test-machine.tailnet.ts.net" : null,
        ip: running ? "100.64.0.1" : null,
      }),
    };
  }

  function setupMocksForSettingsLoad(
    exposureMode: string,
    tailscaleRunning = false,
  ) {
    mockFetch.mockImplementation((url: string) => {
      if (url.includes("/settings/tailscale-status")) {
        return Promise.resolve(mockTailscaleStatusResponse(tailscaleRunning));
      }
      if (url.includes("/settings")) {
        return Promise.resolve(mockSettingsResponse(exposureMode));
      }
      return Promise.reject(new Error(`Unexpected URL: ${url}`));
    });
  }

  test("renders settings page title", async () => {
    setupMocksForSettingsLoad("localhost");

    render(<SettingsPage />);

    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  test("loads and displays current exposure mode", async () => {
    setupMocksForSettingsLoad("localhost");

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText("Exposure Mode")).toBeInTheDocument();
    });

    // Should show localhost as current mode
    await waitFor(() => {
      expect(screen.getByRole("combobox")).toHaveValue("localhost");
    });
  });

  test("shows loading state while fetching settings", () => {
    mockFetch.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<SettingsPage />);

    expect(screen.getByText("Loading settings...")).toBeInTheDocument();
  });

  test("shows error state on fetch failure", async () => {
    mockFetch.mockRejectedValue(new Error("Network error"));

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to load settings/)).toBeInTheDocument();
    });
  });

  test("shows Start Pairing button only in network mode", async () => {
    setupMocksForSettingsLoad("network");

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText("Start Pairing")).toBeInTheDocument();
    });
  });

  test("hides Start Pairing button in localhost mode", async () => {
    setupMocksForSettingsLoad("localhost");

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByRole("combobox")).toHaveValue("localhost");
    });

    expect(screen.queryByText("Start Pairing")).not.toBeInTheDocument();
  });

  test("opens PairingWizard when Start Pairing clicked", async () => {
    setupMocksForSettingsLoad("network");

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText("Start Pairing")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Start Pairing"));

    expect(screen.getByTestId("pairing-wizard")).toBeInTheDocument();
  });

  test("closes PairingWizard when onClose called", async () => {
    setupMocksForSettingsLoad("network");

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText("Start Pairing")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Start Pairing"));
    expect(screen.getByTestId("pairing-wizard")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Close Wizard"));
    expect(screen.queryByTestId("pairing-wizard")).not.toBeInTheDocument();
  });

  test("changes exposure mode via dropdown", async () => {
    let requestCount = 0;
    mockFetch.mockImplementation((url: string, options?: RequestInit) => {
      if (
        url.includes("/settings/exposure-mode") &&
        options?.method === "POST"
      ) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ exposureMode: "network" }),
        });
      }
      if (url.includes("/settings/tailscale-status")) {
        return Promise.resolve(mockTailscaleStatusResponse(false));
      }
      if (url.includes("/settings")) {
        return Promise.resolve(mockSettingsResponse("localhost"));
      }
      return Promise.reject(new Error(`Unexpected URL: ${url}`));
    });

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByRole("combobox")).toHaveValue("localhost");
    });

    fireEvent.change(screen.getByRole("combobox"), {
      target: { value: "network" },
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/settings/exposure-mode"),
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ exposureMode: "network" }),
        }),
      );
    });
  });

  test("shows error when exposure mode change fails", async () => {
    mockFetch.mockImplementation((url: string, options?: RequestInit) => {
      if (
        url.includes("/settings/exposure-mode") &&
        options?.method === "POST"
      ) {
        return Promise.resolve({
          ok: false,
          json: async () => ({ detail: "Failed to update" }),
        });
      }
      if (url.includes("/settings/tailscale-status")) {
        return Promise.resolve(mockTailscaleStatusResponse(false));
      }
      if (url.includes("/settings")) {
        return Promise.resolve(mockSettingsResponse("localhost"));
      }
      return Promise.reject(new Error(`Unexpected URL: ${url}`));
    });

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByRole("combobox")).toHaveValue("localhost");
    });

    fireEvent.change(screen.getByRole("combobox"), {
      target: { value: "network" },
    });

    await waitFor(() => {
      expect(screen.getByText(/Failed to update/)).toBeInTheDocument();
    });
  });

  test("shows pairing success message after completing pairing", async () => {
    setupMocksForSettingsLoad("network");

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText("Start Pairing")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Start Pairing"));
    fireEvent.click(screen.getByText("Complete Pairing"));

    await waitFor(() => {
      expect(
        screen.getByText(/Device paired successfully/),
      ).toBeInTheDocument();
    });
  });

  test("displays Remote Access section description", async () => {
    setupMocksForSettingsLoad("localhost");

    render(<SettingsPage />);

    await waitFor(() => {
      expect(
        screen.getByText(/Control how this server can be accessed/),
      ).toBeInTheDocument();
    });
  });

  test("shows tailscale option when tailscale is running", async () => {
    setupMocksForSettingsLoad("localhost", true);

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByRole("combobox")).toHaveValue("localhost");
    });

    // Check that tailscale option is available
    const select = screen.getByRole("combobox");
    const options = select.querySelectorAll("option");
    const tailscaleOption = Array.from(options).find((opt) =>
      opt.textContent?.includes("Tailscale"),
    );
    expect(tailscaleOption).toBeInTheDocument();
  });

  test("hides tailscale option when tailscale is not running", async () => {
    setupMocksForSettingsLoad("localhost", false);

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByRole("combobox")).toHaveValue("localhost");
    });

    // Check that tailscale option is NOT available
    const select = screen.getByRole("combobox");
    const options = select.querySelectorAll("option");
    const tailscaleOption = Array.from(options).find((opt) =>
      opt.textContent?.includes("Tailscale"),
    );
    expect(tailscaleOption).toBeUndefined();
  });

  test("shows Start Pairing button in tailscale mode", async () => {
    setupMocksForSettingsLoad("tailscale", true);

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText("Start Pairing")).toBeInTheDocument();
    });
  });
});
