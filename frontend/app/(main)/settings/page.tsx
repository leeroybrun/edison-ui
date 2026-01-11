"use client";

import { useCallback, useEffect, useState } from "react";
import { PairingWizard } from "../../../components/Pairing";

/** Settings response from API. */
interface SettingsResponse {
  scanRoots: string[];
  exposureMode: string;
  realtime: {
    enabled: boolean;
    watcherEnabled: boolean;
    pollingIntervalMs: number;
  };
  actor: {
    osUser: string;
    displayName: string | null;
  };
}

/** Tailscale status response from API. */
interface TailscaleStatus {
  installed: boolean;
  running: boolean;
  hostname: string | null;
  ip: string | null;
}

/**
 * Settings page with exposure mode toggle and pairing wizard.
 */
export default function SettingsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [settings, setSettings] = useState<SettingsResponse | null>(null);
  const [exposureMode, setExposureMode] = useState<string>("localhost");
  const [tailscaleStatus, setTailscaleStatus] =
    useState<TailscaleStatus | null>(null);
  const [updating, setUpdating] = useState(false);
  const [updateError, setUpdateError] = useState<string | null>(null);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [pairingSuccess, setPairingSuccess] = useState(false);

  const apiBaseUrl =
    typeof window !== "undefined"
      ? process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
      : "http://localhost:8000";

  // Load settings and tailscale status on mount
  useEffect(() => {
    async function loadSettings() {
      try {
        const [settingsRes, tailscaleRes] = await Promise.all([
          fetch(`${apiBaseUrl}/api/v1/settings`),
          fetch(`${apiBaseUrl}/api/v1/settings/tailscale-status`),
        ]);

        if (!settingsRes.ok) {
          throw new Error("Failed to load settings");
        }
        const data: SettingsResponse = await settingsRes.json();
        setSettings(data);
        setExposureMode(data.exposureMode);

        if (tailscaleRes.ok) {
          const tsData: TailscaleStatus = await tailscaleRes.json();
          setTailscaleStatus(tsData);
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load settings",
        );
      } finally {
        setLoading(false);
      }
    }

    loadSettings();
  }, [apiBaseUrl]);

  // Handle exposure mode change
  const handleExposureModeChange = useCallback(
    async (newMode: string) => {
      setUpdating(true);
      setUpdateError(null);

      try {
        const response = await fetch(
          `${apiBaseUrl}/api/v1/settings/exposure-mode`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ exposureMode: newMode }),
          },
        );

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Failed to update exposure mode");
        }

        setExposureMode(newMode);
      } catch (err) {
        setUpdateError(
          err instanceof Error ? err.message : "Failed to update exposure mode",
        );
        // Revert the select back to current mode
        setExposureMode(exposureMode);
      } finally {
        setUpdating(false);
      }
    },
    [apiBaseUrl, exposureMode],
  );

  // Handle pairing completion
  const handlePaired = useCallback(
    (_result: { token: string; expiresAt: string }) => {
      setWizardOpen(false);
      setPairingSuccess(true);
      // Hide success message after 5 seconds
      setTimeout(() => setPairingSuccess(false), 5000);
    },
    [],
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold text-gray-900">Settings</h1>
        <p className="text-gray-600">Loading settings...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold text-gray-900">Settings</h1>
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-800">
          Failed to load settings: {error}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900">Settings</h1>

      {/* Remote Access Section */}
      <section className="rounded-lg border bg-white p-6 shadow-sm">
        <h2 className="text-lg font-medium text-gray-900">Remote Access</h2>
        <p className="mt-1 text-sm text-gray-600">
          Control how this server can be accessed from other devices.
        </p>

        <div className="mt-4 space-y-4">
          {/* Exposure Mode */}
          <div>
            <label
              className="block text-sm font-medium text-gray-700"
              htmlFor="exposure-mode"
            >
              Exposure Mode
            </label>
            <select
              className="mt-1 block w-full max-w-xs rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              disabled={updating}
              id="exposure-mode"
              onChange={(e) => handleExposureModeChange(e.target.value)}
              value={exposureMode}
            >
              <option value="localhost">Localhost only</option>
              <option value="network">Network (LAN access)</option>
              {tailscaleStatus?.running && (
                <option value="tailscale">
                  Tailscale ({tailscaleStatus.hostname || tailscaleStatus.ip})
                </option>
              )}
            </select>
            <p className="mt-1 text-xs text-gray-500">
              {exposureMode === "localhost" &&
                "Only local connections are allowed"}
              {exposureMode === "network" &&
                "Devices on your local network can connect after pairing"}
              {exposureMode === "tailscale" &&
                "Devices on your Tailscale network can connect after pairing"}
            </p>
          </div>

          {/* Update error */}
          {updateError && (
            <div className="rounded-lg bg-red-50 p-3 text-sm text-red-800">
              {updateError}
            </div>
          )}

          {/* Pairing success message */}
          {pairingSuccess && (
            <div className="rounded-lg bg-green-50 p-3 text-sm text-green-800">
              Device paired successfully! The device can now access this server.
            </div>
          )}

          {/* Start Pairing button - shown in network or tailscale mode */}
          {(exposureMode === "network" || exposureMode === "tailscale") && (
            <div className="pt-2">
              <button
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                onClick={() => setWizardOpen(true)}
                type="button"
              >
                Start Pairing
              </button>
            </div>
          )}
        </div>
      </section>

      {/* Pairing Wizard */}
      <PairingWizard
        apiBaseUrl={`${apiBaseUrl}/api/v1`}
        onClose={() => setWizardOpen(false)}
        onPaired={handlePaired}
        open={wizardOpen}
      />
    </div>
  );
}
