import { AgentsView } from "../../../../components/Agents";
import type {
  TrackingRun,
  AgentsListResponse,
} from "../../../../components/Agents/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface AgentsPageProps {
  params: Promise<{ projectId: string }>;
  searchParams: Promise<{
    sessionId?: string;
    taskId?: string;
    type?: string;
  }>;
}

/**
 * Fetch active agents for a project from the API
 */
async function fetchAgents(
  projectId: string,
  options: {
    sessionId?: string;
    taskId?: string;
    type?: string;
  } = {},
): Promise<{ runs: TrackingRun[]; error?: string }> {
  try {
    const params = new URLSearchParams();
    if (options.sessionId) params.set("sessionId", options.sessionId);
    if (options.taskId) params.set("taskId", options.taskId);
    if (options.type) params.set("type", options.type);

    const queryString = params.toString();
    const url = `${API_BASE_URL}/api/v1/projects/${projectId}/agents/active${queryString ? `?${queryString}` : ""}`;

    const response = await fetch(url, {
      cache: "no-store",
    });

    if (!response.ok) {
      return {
        runs: [],
        error: `Failed to fetch agents: ${response.statusText}`,
      };
    }

    const data: AgentsListResponse = await response.json();
    return { runs: data.items };
  } catch (err) {
    return {
      runs: [],
      error: err instanceof Error ? err.message : "Failed to fetch agents",
    };
  }
}

/**
 * Agents page - displays all active agents/runs for a project.
 *
 * This is a Server Component that fetches data and passes it to
 * the client-side AgentsView component.
 */
export default async function AgentsPage(props: AgentsPageProps) {
  const params = await props.params;
  const searchParams = await props.searchParams;

  const { runs, error } = await fetchAgents(params.projectId, {
    sessionId: searchParams.sessionId,
    taskId: searchParams.taskId,
    type: searchParams.type,
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Agents</h1>
      </div>

      <AgentsView error={error} runs={runs} />
    </div>
  );
}
