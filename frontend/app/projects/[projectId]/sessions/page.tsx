import { SessionsView } from "../../../../components/Sessions";
import type {
  Session,
  SessionListResponse,
  SessionState,
  ViewMode,
} from "../../../../components/Sessions";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface SessionsPageProps {
  params: Promise<{ projectId: string }>;
  searchParams: Promise<{ view?: string; state?: string }>;
}

/**
 * Fetch sessions from API
 */
async function fetchSessions(
  projectId: string,
  state?: SessionState,
): Promise<{ sessions: Session[]; error?: string }> {
  try {
    const params = new URLSearchParams();
    if (state) {
      params.set("state", state);
    }

    const url = `${API_BASE_URL}/api/v1/projects/${projectId}/sessions${params.toString() ? `?${params.toString()}` : ""}`;
    const response = await fetch(url, {
      cache: "no-store", // Disable caching for fresh data
    });

    if (!response.ok) {
      return {
        sessions: [],
        error: `Failed to fetch sessions: ${response.statusText}`,
      };
    }

    const data: SessionListResponse = await response.json();
    return { sessions: data.items };
  } catch (err) {
    return {
      sessions: [],
      error: err instanceof Error ? err.message : "An error occurred",
    };
  }
}

/**
 * Validate view mode from search params
 */
function parseViewMode(view?: string): ViewMode {
  if (view === "board") return "board";
  return "list";
}

/**
 * Validate state filter from search params.
 * Matches backend SESSION_STATES: draft, active, paused, completed, abandoned
 */
function parseStateFilter(state?: string): SessionState | undefined {
  const validStates: SessionState[] = [
    "draft",
    "active",
    "paused",
    "completed",
    "abandoned",
  ];
  if (state && validStates.includes(state as SessionState)) {
    return state as SessionState;
  }
  return undefined;
}

/**
 * Sessions page - displays all sessions for a project.
 *
 * Server component that:
 * - Fetches sessions data from API
 * - Parses URL search params for view mode and filters
 * - Passes data to SessionsView client component
 */
export default async function SessionsPage(props: SessionsPageProps) {
  const params = await props.params;
  const searchParams = await props.searchParams;

  const { projectId } = params;
  const viewMode = parseViewMode(searchParams.view);
  const stateFilter = parseStateFilter(searchParams.state);

  // Fetch sessions - we fetch all and filter client-side for quick filtering
  const { sessions, error } = await fetchSessions(projectId);

  return (
    <SessionsView
      error={error}
      initialStateFilter={stateFilter}
      initialView={viewMode}
      projectId={projectId}
      sessions={sessions}
    />
  );
}
