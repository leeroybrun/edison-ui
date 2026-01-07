"use client";

import { useCallback, useEffect, useState } from "react";

/** Pack list item from API. */
export interface Pack {
  packId: string;
  name: string;
  description?: string;
  enabled: boolean;
  source: string;
}

/** Pack detail from API. */
export interface PackDetail extends Pack {
  config?: Record<string, unknown>;
}

/** Project configuration from API. */
export interface ProjectConfig {
  projectId: string;
  activePacks: string[];
  config: Record<string, unknown>;
}

/** Config preview response from API. */
interface ConfigPreviewResponse {
  valid: boolean;
  preview?: {
    field: string;
    currentValue: unknown;
    newValue: unknown;
  };
  warnings: string[];
  reason?: string;
}

/** Config apply response from API. */
interface ConfigApplyResponse {
  success: boolean;
  auditEntryId?: string;
  backupPath?: string;
  reason?: string;
}

/** Editable field configuration. */
interface EditableField {
  key: string;
  label: string;
  type: "text" | "select";
  options?: string[];
}

// Fields that can be edited via the UI
const EDITABLE_FIELDS: EditableField[] = [
  { key: "displayName", label: "Display Name", type: "text" },
  { key: "exposureMode", label: "Exposure Mode", type: "select", options: ["localhost", "network", "tailscale"] },
  { key: "realtime.pollingIntervalMs", label: "Polling Interval (ms)", type: "text" },
];

export interface ConfigPanelProps {
  /** Project ID to load config for */
  projectId: string;
  /** API base URL */
  apiBaseUrl?: string;
}

/**
 * ConfigPanel displays and allows editing project configuration.
 *
 * Features:
 * - View project config and active packs
 * - Edit allowlisted config fields with preview
 * - View pack details
 */
export function ConfigPanel({
  projectId,
  apiBaseUrl = "http://localhost:8000/api/v1",
}: ConfigPanelProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [config, setConfig] = useState<ProjectConfig | null>(null);
  const [packs, setPacks] = useState<Pack[]>([]);
  const [selectedPack, setSelectedPack] = useState<PackDetail | null>(null);

  // Edit state
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>("");
  const [previewResult, setPreviewResult] = useState<ConfigPreviewResponse | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [isApplying, setIsApplying] = useState(false);

  // Load config and packs
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [configRes, packsRes] = await Promise.all([
        fetch(`${apiBaseUrl}/projects/${projectId}/config`),
        fetch(`${apiBaseUrl}/projects/${projectId}/packs`),
      ]);

      if (!configRes.ok) {
        throw new Error(`Failed to load config: ${configRes.status}`);
      }
      if (!packsRes.ok) {
        throw new Error(`Failed to load packs: ${packsRes.status}`);
      }

      const configData: ProjectConfig = await configRes.json();
      const packsData = await packsRes.json();

      setConfig(configData);
      setPacks(packsData.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load config");
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl, projectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Load pack detail
  const loadPackDetail = useCallback(
    async (packId: string) => {
      try {
        const res = await fetch(`${apiBaseUrl}/projects/${projectId}/packs/${packId}`);
        if (!res.ok) {
          throw new Error(`Failed to load pack: ${res.status}`);
        }
        const data: PackDetail = await res.json();
        setSelectedPack(data);
      } catch (err) {
        console.error("Failed to load pack detail:", err);
      }
    },
    [apiBaseUrl, projectId]
  );

  // Get nested config value
  const getConfigValue = useCallback(
    (field: string): unknown => {
      if (!config) return undefined;
      const parts = field.split(".");
      let current: unknown = config.config;
      for (const part of parts) {
        if (current && typeof current === "object" && part in current) {
          current = (current as Record<string, unknown>)[part];
        } else {
          return undefined;
        }
      }
      return current;
    },
    [config]
  );

  // Start editing a field
  const startEditing = useCallback(
    (field: string) => {
      const value = getConfigValue(field);
      setEditingField(field);
      setEditValue(String(value ?? ""));
      setPreviewResult(null);
    },
    [getConfigValue]
  );

  // Cancel editing
  const cancelEditing = useCallback(() => {
    setEditingField(null);
    setEditValue("");
    setPreviewResult(null);
  }, []);

  // Preview change
  const previewChange = useCallback(async () => {
    if (!editingField) return;

    setIsPreviewLoading(true);
    try {
      const res = await fetch(`${apiBaseUrl}/projects/${projectId}/config/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          field: editingField,
          value: editValue,
        }),
      });

      if (!res.ok) {
        throw new Error(`Preview failed: ${res.status}`);
      }

      const data: ConfigPreviewResponse = await res.json();
      setPreviewResult(data);
    } catch (err) {
      setPreviewResult({
        valid: false,
        reason: err instanceof Error ? err.message : "Preview failed",
        warnings: [],
      });
    } finally {
      setIsPreviewLoading(false);
    }
  }, [apiBaseUrl, projectId, editingField, editValue]);

  // Apply change
  const applyChange = useCallback(async () => {
    if (!editingField || !previewResult?.valid) return;

    setIsApplying(true);
    try {
      const res = await fetch(`${apiBaseUrl}/projects/${projectId}/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          field: editingField,
          value: editValue,
          confirmed: true,
        }),
      });

      if (!res.ok) {
        throw new Error(`Apply failed: ${res.status}`);
      }

      const data: ConfigApplyResponse = await res.json();
      if (data.success) {
        cancelEditing();
        loadData(); // Refresh config
      }
    } catch (err) {
      console.error("Failed to apply change:", err);
    } finally {
      setIsApplying(false);
    }
  }, [apiBaseUrl, projectId, editingField, editValue, previewResult, cancelEditing, loadData]);

  if (loading) {
    return (
      <div className="p-6">
        <p className="text-gray-600">Loading configuration...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-800">
          Error: {error}
        </div>
        <button
          className="mt-4 rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
          onClick={loadData}
          type="button"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Project Configuration</h2>
        <button
          className="rounded-md border border-gray-300 px-3 py-1 text-sm text-gray-700 hover:bg-gray-50"
          onClick={loadData}
          type="button"
        >
          Refresh
        </button>
      </div>

      {/* Display Name */}
      {config && (
        <div className="rounded-lg border bg-white p-4 shadow-sm">
          <h3 className="mb-4 font-medium text-gray-900">
            {String(config.config.displayName || "Unnamed Project")}
          </h3>

          {/* Config Fields */}
          <div className="space-y-4">
            {EDITABLE_FIELDS.map((field) => {
              const value = getConfigValue(field.key);
              return (
                <div
                  className="flex items-center justify-between border-b pb-3 last:border-b-0"
                  key={field.key}
                >
                  <div>
                    <div className="text-sm font-medium text-gray-700">
                      {field.label}
                    </div>
                    <div className="text-sm text-gray-500">
                      {String(value ?? "Not set")}
                    </div>
                  </div>
                  <button
                    className="rounded-md border border-gray-300 px-3 py-1 text-sm text-gray-700 hover:bg-gray-50"
                    onClick={() => startEditing(field.key)}
                    type="button"
                  >
                    Edit
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Packs */}
      <div className="rounded-lg border bg-white p-4 shadow-sm">
        <h3 className="mb-4 font-medium text-gray-900">Active Packs</h3>
        <div className="space-y-2">
          {packs.length === 0 ? (
            <p className="text-sm text-gray-500">No packs configured</p>
          ) : (
            packs.map((pack) => (
              <div
                className="flex cursor-pointer items-center justify-between rounded-md border p-3 hover:bg-gray-50"
                key={pack.packId}
                onClick={() => loadPackDetail(pack.packId)}
              >
                <div>
                  <div className="font-medium text-gray-900">{pack.name}</div>
                  {pack.description && (
                    <div className="text-sm text-gray-500">{pack.description}</div>
                  )}
                </div>
                <span
                  className={`rounded-full px-2 py-1 text-xs ${
                    pack.source === "core"
                      ? "bg-blue-100 text-blue-800"
                      : "bg-gray-100 text-gray-800"
                  }`}
                >
                  {pack.source}
                </span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Pack Detail Panel */}
      {selectedPack && (
        <div className="rounded-lg border bg-white p-4 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-medium text-gray-900">{selectedPack.name}</h3>
            <button
              className="text-sm text-gray-500 hover:text-gray-700"
              onClick={() => setSelectedPack(null)}
              type="button"
            >
              Close
            </button>
          </div>
          {selectedPack.description && (
            <p className="mb-4 text-sm text-gray-600">{selectedPack.description}</p>
          )}
          {selectedPack.config && (
            <pre className="rounded-md bg-gray-100 p-3 text-xs">
              {JSON.stringify(selectedPack.config, null, 2)}
            </pre>
          )}
        </div>
      )}

      {/* Edit Dialog */}
      {editingField && (
        <>
          <div
            className="fixed inset-0 z-50 bg-black/50"
            onClick={cancelEditing}
          />
          <div
            aria-label="Edit configuration"
            className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 transform rounded-lg bg-white p-6 shadow-xl"
            role="dialog"
          >
            <h3 className="mb-4 text-lg font-medium text-gray-900">
              Edit {EDITABLE_FIELDS.find((f) => f.key === editingField)?.label}
            </h3>

            {/* Input */}
            <div className="mb-4">
              {EDITABLE_FIELDS.find((f) => f.key === editingField)?.type === "select" ? (
                <select
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  onChange={(e) => setEditValue(e.target.value)}
                  value={editValue}
                >
                  {EDITABLE_FIELDS.find((f) => f.key === editingField)?.options?.map((opt) => (
                    <option key={opt} value={opt}>
                      {opt}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  onChange={(e) => setEditValue(e.target.value)}
                  type="text"
                  value={editValue}
                />
              )}
            </div>

            {/* Preview Result */}
            {previewResult && (
              <div
                className={`mb-4 rounded-md p-3 text-sm ${
                  previewResult.valid
                    ? "bg-green-50 text-green-800"
                    : "bg-red-50 text-red-800"
                }`}
              >
                {previewResult.valid ? (
                  <>
                    <p>Preview: Change will update the value</p>
                    {previewResult.warnings.length > 0 && (
                      <ul className="mt-2 list-inside list-disc">
                        {previewResult.warnings.map((w, i) => (
                          <li key={i}>{w}</li>
                        ))}
                      </ul>
                    )}
                  </>
                ) : (
                  <p>{previewResult.reason}</p>
                )}
              </div>
            )}

            {/* Buttons */}
            <div className="flex justify-end gap-3">
              <button
                className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                onClick={cancelEditing}
                type="button"
              >
                Cancel
              </button>
              {!previewResult?.valid && (
                <button
                  className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
                  disabled={isPreviewLoading}
                  onClick={previewChange}
                  type="button"
                >
                  {isPreviewLoading ? "Previewing..." : "Preview"}
                </button>
              )}
              {previewResult?.valid && (
                <button
                  className="rounded-md bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700 disabled:opacity-50"
                  disabled={isApplying}
                  onClick={applyChange}
                  type="button"
                >
                  {isApplying ? "Applying..." : "Apply"}
                </button>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
