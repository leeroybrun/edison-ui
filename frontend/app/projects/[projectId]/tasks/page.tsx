import { TasksView } from "../../../../components/Tasks";
import type {
  Task,
  Session,
  TaskListResponse,
} from "../../../../components/Tasks/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface TasksPageProps {
  params: Promise<{ projectId: string }>;
  searchParams: Promise<{
    view?: string;
    state?: string;
    sessionId?: string;
    search?: string;
  }>;
}

/**
 * Fetch tasks for a project from the API
 */
async function fetchTasks(
  projectId: string,
  options: {
    state?: string;
    sessionId?: string;
    search?: string;
  } = {},
): Promise<{ tasks: Task[]; error?: string }> {
  try {
    const params = new URLSearchParams();
    if (options.state) params.set("state", options.state);
    if (options.sessionId) params.set("sessionId", options.sessionId);
    if (options.search) params.set("search", options.search);
    params.set("includeHierarchy", "true");

    const queryString = params.toString();
    const url = `${API_BASE_URL}/api/v1/projects/${projectId}/tasks${queryString ? `?${queryString}` : ""}`;

    const response = await fetch(url, {
      cache: "no-store",
    });

    if (!response.ok) {
      return {
        tasks: [],
        error: `Failed to fetch tasks: ${response.statusText}`,
      };
    }

    const data: TaskListResponse = await response.json();
    return { tasks: data.items };
  } catch (err) {
    return {
      tasks: [],
      error: err instanceof Error ? err.message : "Failed to fetch tasks",
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
 * Tasks page - displays all tasks for a project.
 *
 * This is a Server Component that fetches data and passes it to
 * the client-side TasksView component.
 */
export default async function TasksPage(props: TasksPageProps) {
  const params = await props.params;
  const searchParams = await props.searchParams;

  // Fetch tasks and sessions in parallel
  const [{ tasks, error }, sessions] = await Promise.all([
    fetchTasks(params.projectId, {
      state: searchParams.state,
      sessionId: searchParams.sessionId,
      search: searchParams.search,
    }),
    fetchSessions(params.projectId),
  ]);

  // Determine initial view mode
  const initialView =
    searchParams.view === "board" || searchParams.view === "tree"
      ? searchParams.view
      : "list";

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Tasks</h1>
      </div>

      <TasksView
        error={error}
        initialView={initialView}
        sessions={sessions}
        tasks={tasks}
      />
    </div>
  );
}
