/**
 * Session Context API Route Handler (T070).
 *
 * GET /api/v1/projects/:projectId/sessions/:sessionId/context
 *
 * Returns session context information by calling the Edison CLI:
 * `edison session context --json`
 */
import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

interface RouteParams {
  params: Promise<{
    projectId: string;
    sessionId: string;
  }>;
}

interface SessionContextResponse {
  isEdisonProject: boolean;
  projectRoot: string;
  sessionId: string;
  sessionState: string;
  worktreePath: string | null;
  currentTaskId: string | null;
  currentTaskState: string | null;
  activePacks: string[];
  constitutions: Record<string, string>;
  timestamp?: string;
}

interface ErrorResponse {
  error: string;
  message: string;
}

/**
 * Get project path from project ID.
 * In a real implementation, this would lookup the project path from a registry.
 * For now, we assume the project ID is a path or use a configured projects root.
 */
function getProjectPath(projectId: string): string {
  // Check if projectId is already an absolute path
  if (projectId.startsWith("/")) {
    return projectId;
  }

  // Check for EDISON_PROJECTS_ROOT environment variable
  const projectsRoot = process.env.EDISON_PROJECTS_ROOT;
  if (projectsRoot) {
    return `${projectsRoot}/${projectId}`;
  }

  // Default: assume project ID is relative to home directory
  const home = process.env.HOME || "/tmp";
  return `${home}/projects/${projectId}`;
}

/**
 * Determine error type from CLI error output.
 */
function getErrorType(
  error: Error & { code?: string | number },
  stderr: string
): { status: number; errorCode: string; message: string } {
  const stderrLower = stderr.toLowerCase();

  // Edison CLI not found
  if (error.code === "ENOENT" || stderrLower.includes("command not found")) {
    return {
      status: 503,
      errorCode: "service_unavailable",
      message: "Edison CLI is not available",
    };
  }

  // Session not found
  if (
    stderrLower.includes("not found") ||
    stderrLower.includes("does not exist")
  ) {
    return {
      status: 404,
      errorCode: "not_found",
      message: `Session not found: ${stderr.trim() || error.message}`,
    };
  }

  // Default: internal error
  return {
    status: 500,
    errorCode: "internal_error",
    message: error.message || "An unexpected error occurred",
  };
}

async function handleSessionContext(
  projectId: string,
  sessionId: string
): Promise<NextResponse<SessionContextResponse | ErrorResponse>> {
  const projectPath = getProjectPath(projectId);

  try {
    // Execute Edison CLI command
    const { stdout, stderr } = await execAsync(`edison session context --json`, {
      cwd: projectPath,
      env: {
        ...process.env,
        EDISON_SESSION: sessionId,
      },
    });

    // Log any stderr warnings (non-fatal)
    if (stderr && !stderr.includes("Error")) {
      console.warn(`Edison CLI warning: ${stderr}`);
    }

    // Parse JSON response
    let contextData: SessionContextResponse;
    try {
      contextData = JSON.parse(stdout);
    } catch (parseError) {
      return NextResponse.json(
        {
          error: "internal_error",
          message: `Failed to parse Edison CLI response: ${parseError instanceof Error ? parseError.message : "Invalid JSON"}`,
        },
        { status: 500 }
      );
    }

    // Add timestamp if not present
    if (!contextData.timestamp) {
      contextData.timestamp = new Date().toISOString();
    }

    return NextResponse.json(contextData, { status: 200 });
  } catch (error) {
    const execError = error as Error & {
      code?: string | number;
      stderr?: string;
    };
    const stderr = execError.stderr || "";

    const { status, errorCode, message } = getErrorType(execError, stderr);

    return NextResponse.json(
      {
        error: errorCode,
        message,
      },
      { status }
    );
  }
}

export async function GET(
  _request: NextRequest,
  { params }: RouteParams
): Promise<NextResponse<SessionContextResponse | ErrorResponse>> {
  const { projectId, sessionId } = await params;
  return handleSessionContext(projectId, sessionId);
}
