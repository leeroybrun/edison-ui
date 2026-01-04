import { ActivityPageClient } from "./ActivityPageClient";
import type { ActivityItem, Session, TaskRef, ActivityResponse } from "../../../../components/Activity";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ActivityPageProps {
  params: Promise<{ projectId: string }>;
  searchParams: Promise<{
    sessionId?: string;
    taskId?: string;
    eventType?: string;
    since?: string;
    view?: string;
  }>;
}

/**
 * Fetch activity for a project from the API
 */
async function fetchActivity(
  projectId: string,
  options: {
    sessionId?: string;
    taskId?: string;
    eventType?: string;
    since?: string;
  } = {},
): Promise<{ items: ActivityItem[]; hasMore: boolean; error?: string }> {
  try {
    const params = new URLSearchParams();
    if (options.sessionId) params.set("sessionId", options.sessionId);
    if (options.taskId) params.set("taskId", options.taskId);
    if (options.eventType) params.set("eventType", options.eventType);
    if (options.since) params.set("since", options.since);
    params.set("limit", "50");

    const queryString = params.toString();
    const url = `${API_BASE_URL}/api/v1/projects/${projectId}/activity${queryString ? `?${queryString}` : ""}`;

    const response = await fetch(url, {
      cache: "no-store",
    });

    if (!response.ok) {
      return {
        items: [],
        hasMore: false,
        error: `Failed to fetch activity: ${response.statusText}`,
      };
    }

    const data: ActivityResponse = await response.json();
    return { items: data.items, hasMore: data.hasMore };
  } catch (err) {
    return {
      items: [],
      hasMore: false,
      error: err instanceof Error ? err.message : "Failed to fetch activity",
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
    return data.items.map((session: { sessionId: string; phase?: string }) => ({
      sessionId: session.sessionId,
      name: session.phase || session.sessionId,
    }));
  } catch {
    return [];
  }
}

/**
 * Fetch tasks for a project (for filter dropdown)
 */
async function fetchTasks(projectId: string): Promise<TaskRef[]> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/projects/${projectId}/tasks?limit=100`,
      { cache: "no-store" },
    );

    if (!response.ok) {
      return [];
    }

    const data = await response.json();
    return data.items.map((task: { taskId: string; title: string }) => ({
      taskId: task.taskId,
      title: task.title,
    }));
  } catch {
    return [];
  }
}

/**
 * Activity page - displays project activity timeline.
 *
 * This is a Server Component that fetches data and passes it to
 * the client-side ActivityPageClient component.
 */
export default async function ActivityPage(props: ActivityPageProps) {
  const params = await props.params;
  const searchParams = await props.searchParams;

  // Fetch activity, sessions, and tasks in parallel
  const [{ items, hasMore, error }, sessions, tasks] = await Promise.all([
    fetchActivity(params.projectId, {
      sessionId: searchParams.sessionId,
      taskId: searchParams.taskId,
      eventType: searchParams.eventType,
      since: searchParams.since,
    }),
    fetchSessions(params.projectId),
    fetchTasks(params.projectId),
  ]);

  // Determine initial view mode
  const initialView = searchParams.view === "audit" ? "audit" : "activity";

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Activity</h1>
      </div>

      <ActivityPageClient
        error={error}
        hasMore={hasMore}
        initialFilters={{
          sessionId: searchParams.sessionId,
          taskId: searchParams.taskId,
          eventType: searchParams.eventType,
          since: searchParams.since,
        }}
        initialItems={items}
        initialView={initialView}
        projectId={params.projectId}
        sessions={sessions}
        tasks={tasks}
      />
    </div>
  );
}
