import { QAView } from "../../../../components/QA";
import type { QARecord, QAListResponse, Session } from "../../../../components/QA/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface QAPageProps {
  params: Promise<{ projectId: string }>;
  searchParams: Promise<{
    view?: string;
    state?: string;
    verdict?: string;
    sessionId?: string;
    validator?: string;
    search?: string;
  }>;
}

/**
 * Fetch QA records for a project from the API
 */
async function fetchQARecords(
  projectId: string,
  options: {
    state?: string;
    verdict?: string;
    sessionId?: string;
    search?: string;
  } = {},
): Promise<{ qaRecords: QARecord[]; error?: string }> {
  try {
    const params = new URLSearchParams();
    if (options.state) params.set("state", options.state);
    if (options.verdict) params.set("verdict", options.verdict);
    if (options.sessionId) params.set("sessionId", options.sessionId);
    if (options.search) params.set("search", options.search);

    const queryString = params.toString();
    const url = `${API_BASE_URL}/api/v1/projects/${projectId}/qa${queryString ? `?${queryString}` : ""}`;

    const response = await fetch(url, {
      cache: "no-store",
    });

    if (!response.ok) {
      return {
        qaRecords: [],
        error: `Failed to fetch QA records: ${response.statusText}`,
      };
    }

    const data: QAListResponse = await response.json();
    return { qaRecords: data.items };
  } catch (err) {
    return {
      qaRecords: [],
      error: err instanceof Error ? err.message : "Failed to fetch QA records",
    };
  }
}

/**
 * Fetch sessions for a project (for filter dropdown)
 */
async function fetchSessions(projectId: string): Promise<Session[]> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/projects/${projectId}/sessions`,
      { cache: "no-store" },
    );

    if (!response.ok) {
      return [];
    }

    const data = await response.json();
    // Map sessions to the simplified format for filters
    return data.items.map((session: { sessionId: string; phase?: string }) => ({
      sessionId: session.sessionId,
      name: session.phase || session.sessionId,
    }));
  } catch {
    return [];
  }
}

/**
 * QA page - displays all QA records for a project.
 *
 * This is a Server Component that fetches data and passes it to
 * the client-side QAView component.
 */
export default async function QAPage(props: QAPageProps) {
  const params = await props.params;
  const searchParams = await props.searchParams;

  // Fetch QA records and sessions in parallel
  const [{ qaRecords, error }, sessions] = await Promise.all([
    fetchQARecords(params.projectId, {
      state: searchParams.state,
      verdict: searchParams.verdict,
      sessionId: searchParams.sessionId,
      search: searchParams.search,
    }),
    fetchSessions(params.projectId),
  ]);

  // Determine initial view mode
  const initialView =
    searchParams.view === "board" ? "board" : "list";

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">QA</h1>
      </div>

      <QAView
        error={error}
        initialView={initialView}
        qaRecords={qaRecords}
        sessions={sessions}
      />
    </div>
  );
}
