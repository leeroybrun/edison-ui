"use client";

import type { KeyboardEvent, MouseEvent } from "react";
import { useEffect, useRef, useCallback, useState } from "react";

/** Check if error is a network error (fetch failure). */
function isNetworkError(err: unknown): boolean {
  // In browsers, fetch throws TypeError on network failures
  // In tests, Error with "Network error" message is common
  if (err instanceof TypeError) return true;
  if (err instanceof Error && err.message.toLowerCase().includes("network")) {
    return true;
  }
  return false;
}

/** Pairing start response from API. */
interface PairingStartResponse {
  pairingId: string;
  displayCode: string;
  expiresAt: string;
  qrCodeDataUrl: string;
}

/** Pairing status response from API. */
interface PairingStatusResponse {
  pairingId: string;
  status: "pending" | "completed" | "expired" | "revoked";
  expiresAt: string;
  completed: boolean;
}

/** Props for PairingWizard component. */
export interface PairingWizardProps {
  /** Whether the wizard dialog is open. */
  open: boolean;
  /** Callback when dialog should close. */
  onClose: () => void;
  /** Callback when pairing is successfully completed. */
  onPaired: (result: { token: string; expiresAt: string }) => void;
  /** Base URL for API requests. Defaults to window.location.origin. */
  apiBaseUrl?: string;
}

type WizardStep = "warning" | "pairing" | "success";

/** Polling interval for checking pairing status (ms). */
const STATUS_POLL_INTERVAL_MS = 2000;

/**
 * PairingWizard provides a 3-step wizard for pairing a mobile device.
 *
 * Steps:
 * 1. Warning - Inform user about network exposure risks
 * 2. Pairing - Display code/QR for mobile device to enter (polls for completion)
 * 3. Success - Confirm pairing completed successfully
 *
 * Note: The host UI does NOT call /pairing/complete - only the remote device does.
 * The host UI polls /pairing/{id}/status to detect when the remote device completes.
 */
export function PairingWizard({
  open,
  onClose,
  onPaired,
  apiBaseUrl,
}: PairingWizardProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const [step, setStep] = useState<WizardStep>("warning");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pairingData, setPairingData] = useState<PairingStartResponse | null>(
    null,
  );
  const [countdown, setCountdown] = useState<number>(0);
  const [isExpired, setIsExpired] = useState(false);
  const [isPolling, setIsPolling] = useState(false);

  const baseUrl = apiBaseUrl ?? "http://localhost:8000/api/v1";

  // Reset state when dialog opens
  useEffect(() => {
    if (open) {
      setStep("warning");
      setLoading(false);
      setError(null);
      setPairingData(null);
      setIsExpired(false);
      setIsPolling(false);
      // Focus the dialog for keyboard handling
      dialogRef.current?.focus();
    }
  }, [open]);

  // Global escape key handler
  useEffect(() => {
    if (!open) return;

    const handleGlobalKeyDown = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape" && !loading) {
        onClose();
      }
    };

    document.addEventListener("keydown", handleGlobalKeyDown);
    return () => document.removeEventListener("keydown", handleGlobalKeyDown);
  }, [open, loading, onClose]);

  // Countdown timer for code expiration
  useEffect(() => {
    if (!pairingData?.expiresAt || step !== "pairing") return;

    const updateCountdown = () => {
      const expiresAt = new Date(pairingData.expiresAt).getTime();
      const now = Date.now();
      const remaining = Math.max(0, Math.floor((expiresAt - now) / 1000));
      setCountdown(remaining);

      if (remaining <= 0) {
        setIsExpired(true);
      }
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);

    return () => clearInterval(interval);
  }, [pairingData?.expiresAt, step]);

  // Auto-refresh when code expires
  useEffect(() => {
    if (isExpired && step === "pairing") {
      handleStartPairing();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isExpired, step]);

  // Handle backdrop click
  const handleBackdropClick = useCallback(
    (event: MouseEvent<HTMLDivElement>) => {
      if (event.target === event.currentTarget && !loading) {
        onClose();
      }
    },
    [onClose, loading],
  );

  // Start pairing session
  const handleStartPairing = useCallback(async () => {
    setLoading(true);
    setError(null);
    setIsExpired(false);

    try {
      const response = await fetch(`${baseUrl}/pairing/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || "Failed to start pairing");
      }

      const data: PairingStartResponse = await response.json();
      setPairingData(data);
      setStep("pairing");
    } catch (err) {
      if (isNetworkError(err)) {
        setError("Network error. Please check your connection.");
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to start pairing");
      }
    } finally {
      setLoading(false);
    }
  }, [baseUrl]);

  // Poll for pairing status - detects when remote device completes pairing
  useEffect(() => {
    if (!pairingData || step !== "pairing" || !isPolling) return;

    const pollStatus = async () => {
      try {
        const response = await fetch(
          `${baseUrl}/pairing/${pairingData.pairingId}/status`,
        );

        if (!response.ok) {
          // Stop polling on error
          setIsPolling(false);
          return;
        }

        const data: PairingStatusResponse = await response.json();

        if (data.status === "completed") {
          // Pairing was completed by remote device
          setIsPolling(false);
          setStep("success");
          // Notify parent - we don't have the actual token since remote device got it
          // The host UI just needs to know pairing succeeded
          onPaired({ token: "", expiresAt: data.expiresAt });
        } else if (data.status === "expired") {
          setIsPolling(false);
          setIsExpired(true);
        } else if (data.status === "revoked") {
          setIsPolling(false);
          setError("Pairing was revoked");
        }
        // status === "pending" - keep polling
      } catch {
        // Silently continue polling on network errors
      }
    };

    // Initial poll
    pollStatus();

    // Set up interval
    const interval = setInterval(pollStatus, STATUS_POLL_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [baseUrl, pairingData, step, isPolling, onPaired]);

  // Start polling when user clicks "Start Polling"
  const handleStartPolling = useCallback(() => {
    setIsPolling(true);
  }, []);

  // Proceed from warning to pairing
  const handleUnderstand = useCallback(() => {
    handleStartPairing();
  }, [handleStartPairing]);

  // Refresh pairing code
  const handleRefresh = useCallback(() => {
    handleStartPairing();
  }, [handleStartPairing]);

  // Done - close dialog
  const handleDone = useCallback(() => {
    onClose();
  }, [onClose]);

  // Retry after error
  const handleRetry = useCallback(() => {
    handleStartPairing();
  }, [handleStartPairing]);

  if (!open) {
    return null;
  }

  const titleId = "pairing-dialog-title";

  const formatCountdown = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const getStepNumber = (): number => {
    switch (step) {
      case "warning":
        return 1;
      case "pairing":
        return 2;
      case "success":
        return 3;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50"
        data-testid="dialog-backdrop"
        onClick={handleBackdropClick}
      />

      {/* Dialog */}
      <div
        aria-labelledby={titleId}
        aria-modal="true"
        className="relative z-10 w-full max-w-md rounded-lg bg-white p-6 shadow-xl outline-none"
        ref={dialogRef}
        role="dialog"
        tabIndex={-1}
      >
        {/* Step indicator */}
        <div className="mb-4 text-sm text-gray-500">
          Step {getStepNumber()} of 3
        </div>

        {/* Title */}
        <h2 className="text-lg font-semibold text-gray-900" id={titleId}>
          {step === "warning" && "Remote Access Warning"}
          {step === "pairing" && "Pair Your Device"}
          {step === "success" && "Pairing Complete"}
        </h2>

        {/* Content */}
        <div className="mt-4 space-y-4">
          {/* Step 1: Warning */}
          {step === "warning" && (
            <div className="space-y-4">
              <div className="flex items-start space-x-3 rounded-lg bg-yellow-50 p-4">
                <svg
                  className="h-6 w-6 flex-shrink-0 text-yellow-500"
                  data-testid="warning-icon"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                  />
                </svg>
                <div>
                  <p className="text-sm text-yellow-800">
                    Exposing this server to your network allows remote access
                    from other devices. Only proceed if you trust your network.
                  </p>
                </div>
              </div>
              <p className="text-sm text-gray-600">
                You are about to enable remote access. This will allow paired
                devices on your network to connect to this server.
              </p>
            </div>
          )}

          {/* Loading state between warning and pairing */}
          {step === "warning" && loading && (
            <div className="flex items-center justify-center py-8">
              <svg
                className="h-8 w-8 animate-spin text-blue-600"
                data-testid="loading-spinner"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  fill="currentColor"
                />
              </svg>
            </div>
          )}

          {/* Error state after warning (before reaching pairing) */}
          {step === "warning" && error && !loading && (
            <div className="rounded-lg bg-red-50 p-4 text-sm text-red-800">
              {error}
            </div>
          )}

          {/* Step 2: Pairing */}
          {step === "pairing" && (
            <div className="space-y-4">
              {loading && !pairingData && (
                <div className="flex items-center justify-center py-8">
                  <svg
                    className="h-8 w-8 animate-spin text-blue-600"
                    data-testid="loading-spinner"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      fill="currentColor"
                    />
                  </svg>
                </div>
              )}

              {error && (
                <div className="rounded-lg bg-red-50 p-4 text-sm text-red-800">
                  {error}
                </div>
              )}

              {pairingData && !loading && (
                <>
                  <div className="text-center">
                    <p className="mb-4 text-sm text-gray-600">
                      Enter this code on your mobile device:
                    </p>
                    <div
                      className="mb-4 inline-block rounded-lg bg-gray-100 px-6 py-3 font-mono text-3xl font-bold tracking-wider"
                      data-testid="pairing-code"
                    >
                      {pairingData.displayCode}
                    </div>
                    {isExpired ? (
                      <p className="text-sm text-red-600">
                        Code expired. Generating new code...
                      </p>
                    ) : (
                      <p
                        className="text-sm text-gray-500"
                        data-testid="expiry-countdown"
                      >
                        Expires in {formatCountdown(countdown)}
                      </p>
                    )}
                  </div>

                  <div className="flex justify-center">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      alt="QR code for pairing"
                      className="h-48 w-48 rounded-lg border"
                      src={pairingData.qrCodeDataUrl}
                    />
                  </div>

                  <p className="text-center text-sm text-gray-600">
                    Or scan this QR code with your mobile device
                  </p>
                </>
              )}
            </div>
          )}

          {/* Step 3: Success */}
          {step === "success" && (
            <div className="space-y-4 text-center">
              <div className="flex justify-center">
                <svg
                  className="h-16 w-16 text-green-500"
                  data-testid="success-icon"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                  />
                </svg>
              </div>
              <p className="text-lg font-medium text-gray-900">
                Device paired successfully!
              </p>
              <p className="text-sm text-gray-600">
                Your device is now connected and can access this server
                remotely.
              </p>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="mt-6 flex justify-end gap-3">
          {step === "warning" && (
            <>
              <button
                className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                onClick={onClose}
                type="button"
              >
                Cancel
              </button>
              {error ? (
                <button
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                  onClick={handleRetry}
                  type="button"
                >
                  Retry
                </button>
              ) : (
                <button
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                  disabled={loading}
                  onClick={handleUnderstand}
                  type="button"
                >
                  I Understand
                </button>
              )}
            </>
          )}

          {step === "pairing" && (
            <>
              {error && (
                <button
                  className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                  onClick={handleRetry}
                  type="button"
                >
                  Retry
                </button>
              )}
              {!error && pairingData && (
                <>
                  <button
                    className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                    disabled={loading || isPolling}
                    onClick={handleRefresh}
                    type="button"
                  >
                    Refresh Code
                  </button>
                  {isPolling ? (
                    <div
                      className="inline-flex items-center rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-600"
                      data-testid="waiting-indicator"
                    >
                      <svg
                        className="mr-2 h-4 w-4 animate-spin"
                        data-testid="polling-spinner"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        />
                        <path
                          className="opacity-75"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          fill="currentColor"
                        />
                      </svg>
                      Waiting for device...
                    </div>
                  ) : (
                    <button
                      className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                      disabled={loading}
                      onClick={handleStartPolling}
                      type="button"
                    >
                      I&apos;ve Shared the Code
                    </button>
                  )}
                </>
              )}
            </>
          )}

          {step === "success" && (
            <button
              className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
              onClick={handleDone}
              type="button"
            >
              Done
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
