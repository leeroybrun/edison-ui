"use client";

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

interface PairingResult {
  token: string;
  expiresAt: string;
}

/**
 * Remote pairing page for mobile devices.
 * Accessed via QR code scan with a code query parameter.
 */
export default function PairPage() {
  const searchParams = useSearchParams();
  const codeFromUrl = searchParams.get("code");

  const [code, setCode] = useState(codeFromUrl || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PairingResult | null>(null);

  const apiBaseUrl =
    typeof window !== "undefined"
      ? process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
      : "http://localhost:8000";

  // Auto-submit if code is provided via URL
  useEffect(() => {
    if (codeFromUrl && !result && !loading && !error) {
      handleSubmit(codeFromUrl);
    }
    // Only run once when code is present in URL
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSubmit = useCallback(
    async (displayCode: string) => {
      if (!displayCode.trim()) {
        setError("Please enter the pairing code");
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`${apiBaseUrl}/api/v1/pairing/complete`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ displayCode: displayCode.trim().toUpperCase() }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Failed to complete pairing");
        }

        const data: PairingResult = await response.json();
        setResult(data);

        // Store token in localStorage for subsequent API requests
        if (typeof window !== "undefined") {
          localStorage.setItem("edison_pairing_token", data.token);
          localStorage.setItem("edison_pairing_expires", data.expiresAt);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to complete pairing");
      } finally {
        setLoading(false);
      }
    },
    [apiBaseUrl]
  );

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSubmit(code);
  };

  // Success state
  if (result) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-blue-50 to-white p-4">
        <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-lg">
          <div className="mb-6 flex justify-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
              <svg
                className="h-8 w-8 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M5 13l4 4L19 7"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                />
              </svg>
            </div>
          </div>

          <h1 className="mb-2 text-center text-2xl font-bold text-gray-900">
            Pairing Successful
          </h1>
          <p className="mb-6 text-center text-gray-600">
            This device is now connected to the Edison server.
          </p>

          <div className="rounded-lg bg-gray-50 p-4 text-sm text-gray-600">
            <p>
              <strong>Token expires:</strong>{" "}
              {new Date(result.expiresAt).toLocaleString()}
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Pairing form
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-blue-50 to-white p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-lg">
        <div className="mb-6 flex justify-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-100">
            <svg
              className="h-8 w-8 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
              />
            </svg>
          </div>
        </div>

        <h1 className="mb-2 text-center text-2xl font-bold text-gray-900">
          Pair Device
        </h1>
        <p className="mb-6 text-center text-gray-600">
          Enter the pairing code shown on the host computer to connect this device.
        </p>

        <form onSubmit={handleFormSubmit}>
          <div className="mb-4">
            <label
              className="mb-2 block text-sm font-medium text-gray-700"
              htmlFor="pairing-code"
            >
              Pairing Code
            </label>
            <input
              autoComplete="off"
              autoFocus
              className="w-full rounded-lg border border-gray-300 px-4 py-3 text-center text-2xl font-mono tracking-widest uppercase focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              disabled={loading}
              id="pairing-code"
              maxLength={6}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              placeholder="ABC123"
              type="text"
              value={code}
            />
          </div>

          {error && (
            <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-800">
              {error}
            </div>
          )}

          <button
            className="w-full rounded-lg bg-blue-600 py-3 text-lg font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={loading || !code.trim()}
            type="submit"
          >
            {loading ? "Connecting..." : "Connect"}
          </button>
        </form>
      </div>
    </div>
  );
}
