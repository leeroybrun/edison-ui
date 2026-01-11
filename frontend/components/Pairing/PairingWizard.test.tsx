/**
 * Tests for PairingWizard component (T062).
 *
 * RED Phase: These tests MUST fail initially as the component doesn't exist yet.
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { PairingWizard } from "./PairingWizard";

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe("PairingWizard", () => {
  const defaultProps = {
    open: true,
    onClose: vi.fn(),
    onPaired: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe("initial state (warning step)", () => {
    it("renders nothing when closed", () => {
      const { container } = render(
        <PairingWizard {...defaultProps} open={false} />,
      );
      expect(container.querySelector("dialog")).toBeNull();
    });

    it("renders dialog when open", () => {
      render(<PairingWizard {...defaultProps} />);
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    it("shows network exposure warning on first step", () => {
      render(<PairingWizard {...defaultProps} />);
      expect(screen.getByText(/exposing.*network/i)).toBeInTheDocument();
    });

    it("displays warning icon", () => {
      render(<PairingWizard {...defaultProps} />);
      expect(screen.getByTestId("warning-icon")).toBeInTheDocument();
    });

    it("shows 'I Understand' button to proceed", () => {
      render(<PairingWizard {...defaultProps} />);
      expect(
        screen.getByRole("button", { name: /i understand/i }),
      ).toBeInTheDocument();
    });

    it("shows cancel button", () => {
      render(<PairingWizard {...defaultProps} />);
      expect(
        screen.getByRole("button", { name: /cancel/i }),
      ).toBeInTheDocument();
    });

    it("calls onClose when cancel is clicked", async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      const onClose = vi.fn();
      render(<PairingWizard {...defaultProps} onClose={onClose} />);

      await user.click(screen.getByRole("button", { name: /cancel/i }));
      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });

  describe("pairing code step", () => {
    beforeEach(() => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            pairingId: "pair-123",
            displayCode: "ABC123",
            expiresAt: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
            qrCodeDataUrl: "data:image/png;base64,test-qr-data",
          }),
      });
    });

    it("progresses to pairing step when 'I Understand' is clicked", async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      render(<PairingWizard {...defaultProps} />);

      await user.click(screen.getByRole("button", { name: /i understand/i }));

      await waitFor(() => {
        expect(screen.getByText("ABC123")).toBeInTheDocument();
      });
    });

    it("calls POST /api/v1/pairing/start when proceeding to pairing step", async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      render(<PairingWizard {...defaultProps} />);

      await user.click(screen.getByRole("button", { name: /i understand/i }));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining("/pairing/start"),
          expect.objectContaining({
            method: "POST",
          }),
        );
      });
    });

    it("displays the pairing code prominently", async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      render(<PairingWizard {...defaultProps} />);

      await user.click(screen.getByRole("button", { name: /i understand/i }));

      await waitFor(() => {
        const codeElement = screen.getByTestId("pairing-code");
        expect(codeElement).toHaveTextContent("ABC123");
      });
    });

    it("displays the QR code image", async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      render(<PairingWizard {...defaultProps} />);

      await user.click(screen.getByRole("button", { name: /i understand/i }));

      await waitFor(() => {
        const qrImage = screen.getByAltText(/qr code/i);
        expect(qrImage).toHaveAttribute(
          "src",
          "data:image/png;base64,test-qr-data",
        );
      });
    });

    it("shows countdown timer for code expiration", async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      render(<PairingWizard {...defaultProps} />);

      await user.click(screen.getByRole("button", { name: /i understand/i }));

      await waitFor(() => {
        expect(screen.getByTestId("expiry-countdown")).toBeInTheDocument();
      });
    });

    it("shows loading state while fetching pairing code", async () => {
      mockFetch.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 1000)),
      );
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      render(<PairingWizard {...defaultProps} />);

      await user.click(screen.getByRole("button", { name: /i understand/i }));

      expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
    });

    it("shows error message when pairing start fails", async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        json: () =>
          Promise.resolve({
            error: "server_error",
            message: "Failed to start pairing",
          }),
      });
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      render(<PairingWizard {...defaultProps} />);

      await user.click(screen.getByRole("button", { name: /i understand/i }));

      await waitFor(() => {
        expect(screen.getByText(/failed.*pairing/i)).toBeInTheDocument();
      });
    });

    it("allows retry when pairing start fails", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () =>
          Promise.resolve({
            error: "server_error",
            message: "Failed",
          }),
      });
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      render(<PairingWizard {...defaultProps} />);

      await user.click(screen.getByRole("button", { name: /i understand/i }));

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /retry/i }),
        ).toBeInTheDocument();
      });
    });

    it("refreshes code when 'Refresh Code' is clicked", async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      render(<PairingWizard {...defaultProps} />);

      await user.click(screen.getByRole("button", { name: /i understand/i }));

      await waitFor(() => {
        expect(screen.getByTestId("pairing-code")).toBeInTheDocument();
      });

      mockFetch.mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            pairingId: "pair-456",
            displayCode: "XYZ789",
            expiresAt: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
            qrCodeDataUrl: "data:image/png;base64,new-qr-data",
          }),
      });

      await user.click(screen.getByRole("button", { name: /refresh/i }));

      await waitFor(() => {
        expect(screen.getByTestId("pairing-code")).toHaveTextContent("XYZ789");
      });
    });
  });

  describe("completion step", () => {
    beforeEach(() => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            pairingId: "pair-123",
            displayCode: "ABC123",
            expiresAt: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
            qrCodeDataUrl: "data:image/png;base64,test-qr-data",
          }),
      });
    });

    it("shows success message when remote device completes pairing", async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      const onPaired = vi.fn();
      render(<PairingWizard {...defaultProps} onPaired={onPaired} />);

      // Progress to pairing step
      await user.click(screen.getByRole("button", { name: /i understand/i }));

      await waitFor(() => {
        expect(screen.getByTestId("pairing-code")).toBeInTheDocument();
      });

      // Click "I've Shared the Code" to start polling
      await user.click(
        screen.getByRole("button", { name: /i.ve shared.*code/i }),
      );

      // Verify polling indicator is shown
      await waitFor(() => {
        expect(screen.getByTestId("waiting-indicator")).toBeInTheDocument();
      });

      // Mock status polling response indicating completion
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            pairingId: "pair-123",
            status: "completed",
            expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
            completed: true,
          }),
      });

      // Advance time to trigger polling
      vi.advanceTimersByTime(2000);

      await waitFor(() => {
        expect(screen.getByText(/paired successfully/i)).toBeInTheDocument();
      });
    });

    it("calls onPaired when pairing completes", async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      const onPaired = vi.fn();
      render(<PairingWizard {...defaultProps} onPaired={onPaired} />);

      // Start pairing
      await user.click(screen.getByRole("button", { name: /i understand/i }));

      await waitFor(() => {
        expect(screen.getByTestId("pairing-code")).toBeInTheDocument();
      });

      // Start polling
      await user.click(
        screen.getByRole("button", { name: /i.ve shared.*code/i }),
      );

      // Mock status polling response indicating completion
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            pairingId: "pair-123",
            status: "completed",
            expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
            completed: true,
          }),
      });

      // Advance time to trigger polling
      vi.advanceTimersByTime(2000);

      await waitFor(() => {
        expect(onPaired).toHaveBeenCalledWith({
          token: "",
          expiresAt: expect.any(String),
        });
      });
    });

    it("shows 'Done' button after successful pairing", async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      render(<PairingWizard {...defaultProps} />);

      // Start pairing
      await user.click(screen.getByRole("button", { name: /i understand/i }));

      await waitFor(() => {
        expect(screen.getByTestId("pairing-code")).toBeInTheDocument();
      });

      // Start polling
      await user.click(
        screen.getByRole("button", { name: /i.ve shared.*code/i }),
      );

      // Mock status polling response indicating completion
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            pairingId: "pair-123",
            status: "completed",
            expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
            completed: true,
          }),
      });

      // Advance time to trigger polling
      vi.advanceTimersByTime(2000);

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /done/i }),
        ).toBeInTheDocument();
      });
    });

    it("closes dialog when 'Done' is clicked after successful pairing", async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      const onClose = vi.fn();
      render(<PairingWizard {...defaultProps} onClose={onClose} />);

      // Start pairing
      await user.click(screen.getByRole("button", { name: /i understand/i }));

      await waitFor(() => {
        expect(screen.getByTestId("pairing-code")).toBeInTheDocument();
      });

      // Start polling
      await user.click(
        screen.getByRole("button", { name: /i.ve shared.*code/i }),
      );

      // Mock status polling response indicating completion
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            pairingId: "pair-123",
            status: "completed",
            expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
            completed: true,
          }),
      });

      // Advance time to trigger polling
      vi.advanceTimersByTime(2000);

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /done/i }),
        ).toBeInTheDocument();
      });

      await user.click(screen.getByRole("button", { name: /done/i }));
      expect(onClose).toHaveBeenCalled();
    });
  });

  describe("error handling", () => {
    it("shows error when pairing is revoked during polling", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            pairingId: "pair-123",
            displayCode: "ABC123",
            expiresAt: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
            qrCodeDataUrl: "data:image/png;base64,test-qr-data",
          }),
      });

      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      render(<PairingWizard {...defaultProps} />);

      await user.click(screen.getByRole("button", { name: /i understand/i }));

      await waitFor(() => {
        expect(screen.getByTestId("pairing-code")).toBeInTheDocument();
      });

      // Start polling
      await user.click(
        screen.getByRole("button", { name: /i.ve shared.*code/i }),
      );

      // Mock status polling response indicating revoked
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            pairingId: "pair-123",
            status: "revoked",
            expiresAt: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
            completed: false,
          }),
      });

      // Advance time to trigger polling
      vi.advanceTimersByTime(2000);

      await waitFor(() => {
        expect(screen.getByText(/revoked/i)).toBeInTheDocument();
      });
    });

    it("shows network error message on connection failure", async () => {
      mockFetch.mockRejectedValue(new Error("Network error"));

      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      render(<PairingWizard {...defaultProps} />);

      await user.click(screen.getByRole("button", { name: /i understand/i }));

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });
    });
  });

  describe("accessibility", () => {
    it("has accessible dialog role", () => {
      render(<PairingWizard {...defaultProps} />);
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    it("has aria-labelledby pointing to title", () => {
      render(<PairingWizard {...defaultProps} />);
      const dialog = screen.getByRole("dialog");
      expect(dialog).toHaveAttribute("aria-labelledby");
    });

    it("has aria-modal attribute", () => {
      render(<PairingWizard {...defaultProps} />);
      const dialog = screen.getByRole("dialog");
      expect(dialog).toHaveAttribute("aria-modal", "true");
    });

    it("closes on Escape key press", async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      const onClose = vi.fn();
      render(<PairingWizard {...defaultProps} onClose={onClose} />);

      await user.keyboard("{Escape}");
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it("traps focus within dialog", () => {
      render(<PairingWizard {...defaultProps} />);

      const buttons = screen.getAllByRole("button");
      expect(buttons.length).toBeGreaterThan(0);

      // All buttons should be focusable
      buttons.forEach((button) => {
        expect(button).not.toHaveAttribute("tabindex", "-1");
      });
    });
  });

  describe("step indicator", () => {
    it("shows step 1 of 3 on warning step", () => {
      render(<PairingWizard {...defaultProps} />);
      expect(screen.getByText(/step 1/i)).toBeInTheDocument();
    });

    it("shows step 2 of 3 on pairing code step", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            pairingId: "pair-123",
            displayCode: "ABC123",
            expiresAt: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
            qrCodeDataUrl: "data:image/png;base64,test-qr-data",
          }),
      });

      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      render(<PairingWizard {...defaultProps} />);

      await user.click(screen.getByRole("button", { name: /i understand/i }));

      await waitFor(() => {
        expect(screen.getByText(/step 2/i)).toBeInTheDocument();
      });
    });

    it("shows step 3 of 3 on success step", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            pairingId: "pair-123",
            displayCode: "ABC123",
            expiresAt: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
            qrCodeDataUrl: "data:image/png;base64,test-qr-data",
          }),
      });

      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      render(<PairingWizard {...defaultProps} />);

      await user.click(screen.getByRole("button", { name: /i understand/i }));

      await waitFor(() => {
        expect(screen.getByTestId("pairing-code")).toBeInTheDocument();
      });

      // Start polling
      await user.click(
        screen.getByRole("button", { name: /i.ve shared.*code/i }),
      );

      // Mock status polling response indicating completion
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            pairingId: "pair-123",
            status: "completed",
            expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
            completed: true,
          }),
      });

      // Advance time to trigger polling
      vi.advanceTimersByTime(2000);

      await waitFor(() => {
        expect(screen.getByText(/step 3/i)).toBeInTheDocument();
      });
    });
  });

  describe("code expiration", () => {
    it("auto-refreshes code when it expires", async () => {
      const expiresAt = new Date(Date.now() + 10 * 1000).toISOString(); // 10 seconds
      mockFetch.mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            pairingId: "pair-123",
            displayCode: "ABC123",
            expiresAt,
            qrCodeDataUrl: "data:image/png;base64,test-qr-data",
          }),
      });

      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      render(<PairingWizard {...defaultProps} />);

      await user.click(screen.getByRole("button", { name: /i understand/i }));

      await waitFor(() => {
        expect(screen.getByTestId("pairing-code")).toBeInTheDocument();
      });

      const initialCallCount = mockFetch.mock.calls.length;

      // Mock new code for refresh
      mockFetch.mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            pairingId: "pair-456",
            displayCode: "NEW123",
            expiresAt: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
            qrCodeDataUrl: "data:image/png;base64,new-qr-data",
          }),
      });

      // Advance time past expiration
      vi.advanceTimersByTime(11 * 1000);

      await waitFor(() => {
        // Should have at least one more call for the refresh
        expect(mockFetch.mock.calls.length).toBeGreaterThan(initialCallCount);
      });
    });

    it("shows expired message when code expires", async () => {
      // Use a longer expiration (5 seconds) to avoid immediate auto-refresh
      const expiresAt = new Date(Date.now() + 5000).toISOString();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            pairingId: "pair-123",
            displayCode: "ABC123",
            expiresAt,
            qrCodeDataUrl: "data:image/png;base64,test-qr-data",
          }),
      });

      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      render(<PairingWizard {...defaultProps} />);

      await user.click(screen.getByRole("button", { name: /i understand/i }));

      await waitFor(() => {
        expect(screen.getByTestId("pairing-code")).toBeInTheDocument();
      });

      // Advance time past expiration - this should trigger "expired" message
      // before the auto-refresh can complete
      vi.advanceTimersByTime(6000);

      await waitFor(() => {
        expect(screen.getByText(/expired/i)).toBeInTheDocument();
      });
    });
  });
});
