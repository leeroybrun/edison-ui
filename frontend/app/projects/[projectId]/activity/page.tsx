import { ActivityPageClient } from "./ActivityPageClient";
import type {
  ActivityItem,
  AuditEvent,
  AuditResponse,
  Session,
  TaskRef,
  ActivityResponse,
} from "../../../../components/Activity";

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
 * Fetch audit events for a project from the API
 */
async function fetchAudit(
  projectId: string,
  options: {
    sessionId?: string;
    invocationId?: string;
    since?: string;
  } = {},
): Promise<{ items: AuditEvent[]; hasMore: boolean; error?: string }> {
  try {
    const params = new URLSearchParams();
    if (options.sessionId) params.set("sessionId", options.sessionId);
    if (options.invocationId) params.set("invocationId", options.invocationId);
    if (options.since) params.set("since", options.since);
    params.set("limit", "50");

    const queryString = params.toString();
    const url = `${API_BASE_URL}/api/v1/projects/${projectId}/audit${queryString ? `?${queryString}` : ""}`;

    const response = await fetch(url, {
      cache: "no-store",
    });

    if (!response.ok) {
      return {
        items: [],
        hasMore: false,
        error: `Failed to fetch audit: ${response.statusText}`,
      };
    }

    const data: AuditResponse = await response.json();
    return { items: data.items, hasMore: data.hasMore };
  } catch (err) {
    return {
      items: [],
      hasMore: false,
      error: err instanceof Error ? err.message : "Failed to fetch audit",
    };
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

  // Determine initial view mode
  const initialView = searchParams.view === "audit" ? "audit" : "activity";

  // Fetch data based on the view
  const [activityResult, auditResult, sessions, tasks] = await Promise.all([
    initialView === "activity"
      ? fetchActivity(params.projectId, {
          sessionId: searchParams.sessionId,
          taskId: searchParams.taskId,
          eventType: searchParams.eventType,
          since: searchParams.since,
        })
      : Promise.resolve({ items: [] as ActivityItem[], hasMore: false, error: undefined }),
    initialView === "audit"
      ? fetchAudit(params.projectId, {
          sessionId: searchParams.sessionId,
          since: searchParams.since,
        })
      : Promise.resolve({ items: [] as AuditEvent[], hasMore: false, error: undefined }),
    fetchSessions(params.projectId),
    fetchTasks(params.projectId),
  ]);

  // Get the appropriate items, hasMore, and error based on view
  const items = initialView === "audit" ? auditResult.items : activityResult.items;
  const hasMore = initialView === "audit" ? auditResult.hasMore : activityResult.hasMore;
  const error = initialView === "audit" ? auditResult.error : activityResult.error;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Activity</h1>
      </div>

      <ActivityPageClient
        error={error}
        hasMore={hasMore}
        initialActivityItems={initialView === "activity" ? items as ActivityItem[] : []}
        initialAuditItems={initialView === "audit" ? items as AuditEvent[] : []}
        initialFilters={{
          sessionId: searchParams.sessionId,
          taskId: searchParams.taskId,
          eventType: searchParams.eventType,
          since: searchParams.since,
        }}
        initialView={initialView}
        projectId={params.projectId}
        sessions={sessions}
        tasks={tasks}
      />
    </div>
  );
}
