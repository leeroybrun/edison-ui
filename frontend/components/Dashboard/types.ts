/**
 * Dashboard types matching backend API schemas.
 */

export interface ProjectHealth {
  taskCount: number;
  sessionCount: number;
  qaCount: number;
  activeCount: number;
}

export interface Project {
  projectId: string;
  path: string;
  name: string;
  pinned: boolean;
  health: ProjectHealth;
  lastActivityAt: string | null;
  hasGit: boolean;
  errors: string[];
}

export interface ProjectListResponse {
  items: Project[];
  total: number;
  limit: number;
  offset: number;
}
