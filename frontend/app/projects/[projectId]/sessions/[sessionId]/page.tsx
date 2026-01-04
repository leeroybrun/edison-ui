import Link from "next/link";

import { TasksView } from "../../../../../components/Tasks";
import type {
  Task,
  Session,
  TaskListResponse,
} from "../../../../../components/Tasks/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface SessionTasksPageProps {
  params: Promise<{ projectId: string; sessionId: string }>;
  searchParams: Promise<{
    view?: string;
    state?: string;
    search?: string;
  }>;
}

/**
 * Fetch a single session's details from the API
 */
async function fetchSession(
  projectId: string,
  sessionId: string
): Promise<{ session: Session | null; error?: string }> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/projects/${projectId}/sessions/${sessionId}`,
      { cache: "no-store" }
    );

    if (!response.ok) {
      return {
        session: null,
        error: `Failed to fetch session: ${response.statusText}`,
      };
    }

    const data = await response.json();
    return {
      session: {
        sessionId: data.sessionId,
        name: data.phase || data.sessionId,
      },
    };
  } catch (err) {
    return {
      session: null,
      error: err instanceof Error ? err.message : "Failed to fetch session",
    };
  }
}

/**
 * Fetch tasks for a specific session from the API
 */
async function fetchSessionTasks(
  projectId: string,
  sessionId: string,
  options: {
    state?: string;
    search?: string;
  } = {}
): Promise<{ tasks: Task[]; error?: string }> {
  try {
    const params = new URLSearchParams();
    params.set("sessionId", sessionId);
    if (options.state) params.set("state", options.state);
    if (options.search) params.set("search", options.search);
    params.set("includeHierarchy", "true");

    const url = `${API_BASE_URL}/api/v1/projects/${projectId}/tasks?${params.toString()}`;

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
 * Session Tasks page - displays all tasks for a specific session.
 *
 * This page reuses the TasksView component with a locked session filter.
 * The session filter dropdown is hidden since we're in a session-specific context.
 * Users can still filter by state and search within the session's tasks.
 */
export default async function SessionTasksPage(props: SessionTasksPageProps) {
  const params = await props.params;
  const searchParams = await props.searchParams;

  // Fetch session details and tasks in parallel
  const [{ session, error: sessionError }, { tasks, error: tasksError }] =
    await Promise.all([
      fetchSession(params.projectId, params.sessionId),
      fetchSessionTasks(params.projectId, params.sessionId, {
        state: searchParams.state,
        search: searchParams.search,
      }),
    ]);

  // Combine errors for display
  const error = sessionError || tasksError;

  // Determine initial view mode
  const initialView =
    searchParams.view === "board" || searchParams.view === "tree"
      ? searchParams.view
      : "list";

  return (
    <div className="space-y-4">
      {/* Header with breadcrumb and session info */}
      <div className="flex flex-col gap-2">
        <nav aria-label="Breadcrumb" className="text-sm">
          <ol className="flex items-center gap-2">
            <li>
              <Link
                className="text-gray-500 hover:text-gray-700"
                href={`/projects/${params.projectId}/sessions`}
              >
                Sessions
              </Link>
            </li>
            <li className="text-gray-400">/</li>
            <li className="font-medium text-gray-900">{params.sessionId}</li>
          </ol>
        </nav>
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">
            Session Tasks
          </h1>
          {session && (
            <span className="rounded-md bg-blue-50 px-3 py-1 text-sm text-blue-700">
              {session.name}
            </span>
          )}
        </div>
      </div>

      <TasksView
        error={error}
        initialView={initialView}
        lockedSessionId={params.sessionId}
        sessions={[]}
        tasks={tasks}
      />
    </div>
  );
}
