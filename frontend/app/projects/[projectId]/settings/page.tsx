"use client";

import { useParams } from "next/navigation";

import { ConfigPanel } from "../../../../components/Config";

/**
 * Project settings page (T077).
 *
 * Displays project configuration and pack management using the ConfigPanel component.
 * Connects to:
 * - GET /projects/{projectId}/config
 * - GET /projects/{projectId}/packs
 * - GET /projects/{projectId}/packs/{packId}
 * - POST /projects/{projectId}/config/preview
 * - POST /projects/{projectId}/config
 */
export default function SettingsPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;

  // Get API base URL from environment or default (base origin, component expects /api/v1)
  const apiOrigin = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const apiBaseUrl = `${apiOrigin}/api/v1`;

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Settings</h1>
      <ConfigPanel projectId={projectId} apiBaseUrl={apiBaseUrl} />
    </div>
  );
}
