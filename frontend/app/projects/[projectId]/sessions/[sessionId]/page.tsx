import Link from "next/link";

import { TasksView } from "../../../../../components/Tasks";
import type {
  Task,
  Session,
  TaskListResponse,
} from "../../../../../components/Tasks/types";
import { QAView } from "../../../../../components/QA";
import type {
  QARecord,
  QAListResponse,
} from "../../../../../components/QA/types";
import { EntityAuditPanel } from "../../../../../components/Activity";
import { SessionContextPanel } from "../../../../../components/Sessions/SessionContextPanel";
import { SessionNextPanel } from "../../../../../components/Sessions/SessionNextPanel";
import { SessionDetailTabs, type SessionDetailTab } from "./SessionDetailTabs";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface SessionDetailPageProps {
  params: Promise<{ projectId: string; sessionId: string }>;
  searchParams: Promise<{
    tab?: string;
    view?: string;
    state?: string;
    search?: string;
    verdict?: string;
  }>;
}

/**
 * Fetch a single session's details from the API
 */
async function fetchSession(
  projectId: string,
  sessionId: string,
): Promise<{ session: Session | null; error?: string }> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/projects/${projectId}/sessions/${sessionId}`,
      { cache: "no-store" },
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
  } = {},
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
 * Fetch QA records for a specific session from the API
 */
async function fetchSessionQA(
  projectId: string,
  sessionId: string,
  options: {
    state?: string;
    verdict?: string;
    search?: string;
  } = {},
): Promise<{ qaRecords: QARecord[]; error?: string }> {
  try {
    const params = new URLSearchParams();
    params.set("sessionId", sessionId);
    if (options.state) params.set("state", options.state);
    if (options.verdict) params.set("verdict", options.verdict);

    const url = `${API_BASE_URL}/api/v1/projects/${projectId}/qa?${params.toString()}`;

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
 * Determine active tab from search params.
 */
function getActiveTab(tab?: string): SessionDetailTab {
  if (tab === "qa" || tab === "activity" || tab === "context" || tab === "next") {
    return tab;
  }
  return "tasks";
}

/**
 * Session Detail page - displays tasks, QA, context, and next for a specific session.
 *
 * This page provides a tabbed interface for viewing session-scoped:
 * - Tasks (using TasksView with locked session filter)
 * - QA records (using QAView with locked session filter)
 * - Context (session configuration and state information)
 * - Next (recommended next steps and suggested actions)
 *
 * Both Tasks and QA views hide the session filter dropdown since we're in a session-specific context.
 * Users can still filter by state, verdict, and search within the session.
 */
export default async function SessionDetailPage(props: SessionDetailPageProps) {
  const params = await props.params;
  const searchParams = await props.searchParams;

  // Determine active tab (default to tasks)
  const activeTab = getActiveTab(searchParams.tab);

  // Fetch session details, tasks, and QA in parallel
  const [
    { session, error: sessionError },
    { tasks, error: tasksError },
    { qaRecords, error: qaError },
  ] = await Promise.all([
    fetchSession(params.projectId, params.sessionId),
    fetchSessionTasks(params.projectId, params.sessionId, {
      state: activeTab === "tasks" ? searchParams.state : undefined,
      search: activeTab === "tasks" ? searchParams.search : undefined,
    }),
    fetchSessionQA(params.projectId, params.sessionId, {
      state: activeTab === "qa" ? searchParams.state : undefined,
      verdict: activeTab === "qa" ? searchParams.verdict : undefined,
    }),
  ]);

  // Determine initial view mode for tasks
  const tasksInitialView =
    searchParams.view === "board" || searchParams.view === "tree"
      ? searchParams.view
      : "list";

  // Determine initial view mode for QA (list or board)
  const qaInitialView = searchParams.view === "board" ? "board" : "list";

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
          <h1 className="text-2xl font-bold text-gray-900">Session Detail</h1>
          {session && (
            <span className="rounded-md bg-blue-50 px-3 py-1 text-sm text-blue-700">
              {session.name}
            </span>
          )}
        </div>
      </div>

      {/* Tab navigation */}
      <SessionDetailTabs
        activeTab={activeTab}
        projectId={params.projectId}
        sessionId={params.sessionId}
        taskCount={tasks.length}
        qaCount={qaRecords.length}
      />

      {/* Tab content */}
      {activeTab === "tasks" && (
        <TasksView
          error={sessionError || tasksError}
          initialView={tasksInitialView}
          lockedSessionId={params.sessionId}
          sessions={[]}
          tasks={tasks}
        />
      )}
      {activeTab === "qa" && (
        <QAView
          error={sessionError || qaError}
          initialView={qaInitialView}
          lockedSessionId={params.sessionId}
          qaRecords={qaRecords}
          sessions={[]}
        />
      )}
      {activeTab === "activity" && (
        <EntityAuditPanel
          entityId={params.sessionId}
          entityType="session"
          projectId={params.projectId}
        />
      )}
      {activeTab === "context" && (
        <SessionContextPanel
          projectId={params.projectId}
          sessionId={params.sessionId}
        />
      )}
      {activeTab === "next" && (
        <SessionNextPanel
          projectId={params.projectId}
          sessionId={params.sessionId}
        />
      )}
    </div>
  );
}
