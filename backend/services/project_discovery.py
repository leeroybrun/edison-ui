"""Project discovery service (T010).

Discovers Edison projects in configured scan roots and collects health metrics.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class ProjectHealth:
    """Health counts for a project."""

    task_count: int = 0
    session_count: int = 0
    qa_count: int = 0
    active_count: int = 0


@dataclass
class DiscoveredProject:
    """A discovered Edison project."""

    project_id: str
    path: str
    name: str
    pinned: bool = False
    health: ProjectHealth = field(default_factory=ProjectHealth)
    last_activity_at: str | None = None
    has_git: bool = False
    errors: list[str] = field(default_factory=list)


class ProjectDiscoveryService:
    """Service for discovering Edison projects in scan roots."""

    def __init__(
        self,
        scan_roots: list[str],
        ignore_patterns: list[str] | None = None,
        pin_storage_path: str | None = None,
    ) -> None:
        """Initialize the discovery service.

        Args:
            scan_roots: List of directory paths to scan for Edison projects.
            ignore_patterns: Patterns to ignore during scanning.
            pin_storage_path: Path to JSON file storing pinned projects.
        """
        self.scan_roots = [Path(root).expanduser().resolve() for root in scan_roots]
        self.ignore_patterns = ignore_patterns or [
            "node_modules",
            ".git",
            ".venv",
            "__pycache__",
        ]
        self.pin_storage_path = (
            Path(pin_storage_path).expanduser().resolve() if pin_storage_path else None
        )
        self._pinned_projects: set[str] = set()
        self._load_pinned_projects()

    def _load_pinned_projects(self) -> None:
        """Load pinned project IDs from storage."""
        if self.pin_storage_path and self.pin_storage_path.exists():
            try:
                with open(self.pin_storage_path) as f:
                    data = json.load(f)
                    self._pinned_projects = set(data.get("pinned", []))
            except (json.JSONDecodeError, OSError):
                self._pinned_projects = set()

    def _save_pinned_projects(self) -> None:
        """Save pinned project IDs to storage."""
        if self.pin_storage_path:
            self.pin_storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.pin_storage_path, "w") as f:
                json.dump({"pinned": list(self._pinned_projects)}, f)

    def _generate_project_id(self, path: Path) -> str:
        """Generate a stable project ID from path.

        Uses first 12 chars of SHA-256 hash of the resolved path.
        """
        path_str = str(path.resolve())
        return hashlib.sha256(path_str.encode()).hexdigest()[:12]

    def _is_edison_project(self, path: Path) -> bool:
        """Check if a directory is an Edison project."""
        edison_dir = path / ".edison"
        return edison_dir.is_dir()

    def _has_git(self, path: Path) -> bool:
        """Check if a directory is a git repository."""
        git_dir = path / ".git"
        return git_dir.is_dir()

    def _should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored."""
        return path.name in self.ignore_patterns

    def _count_files_in_state(self, state_dir: Path) -> int:
        """Count .md files in a state directory."""
        if not state_dir.exists():
            return 0
        return sum(1 for f in state_dir.iterdir() if f.suffix == ".md")

    def _get_health(self, project_path: Path) -> ProjectHealth:
        """Get health counts for a project."""
        project_dir = project_path / ".project"
        if not project_dir.exists():
            return ProjectHealth()

        # Count tasks
        tasks_dir = project_dir / "tasks"
        task_count = 0
        if tasks_dir.exists():
            for state in ["todo", "wip", "blocked", "done", "validated"]:
                task_count += self._count_files_in_state(tasks_dir / state)

        # Count sessions
        sessions_dir = project_dir / "sessions"
        session_count = 0
        active_count = 0
        if sessions_dir.exists():
            for state_dir in sessions_dir.iterdir():
                if state_dir.is_dir():
                    for session_dir in state_dir.iterdir():
                        if (
                            session_dir.is_dir()
                            and (session_dir / "session.json").exists()
                        ):
                            session_count += 1
                            if state_dir.name == "active":
                                active_count += 1

        # Count QA
        qa_dir = project_dir / "qa"
        qa_count = 0
        if qa_dir.exists():
            for state in ["waiting", "todo", "wip", "done", "validated"]:
                qa_count += self._count_files_in_state(qa_dir / state)

        return ProjectHealth(
            task_count=task_count,
            session_count=session_count,
            qa_count=qa_count,
            active_count=active_count,
        )

    def _get_last_activity(self, project_path: Path) -> str | None:
        """Get the last activity timestamp for a project."""
        project_dir = project_path / ".project"
        if not project_dir.exists():
            return None

        # Look for latest modification in logs or tasks
        latest_mtime: float | None = None

        logs_dir = project_dir / "logs" / "edison"
        if logs_dir.exists():
            for log_file in logs_dir.glob("*.jsonl"):
                mtime = log_file.stat().st_mtime
                if latest_mtime is None or mtime > latest_mtime:
                    latest_mtime = mtime

        # Also check tasks directory
        tasks_dir = project_dir / "tasks"
        if tasks_dir.exists():
            for md_file in tasks_dir.rglob("*.md"):
                mtime = md_file.stat().st_mtime
                if latest_mtime is None or mtime > latest_mtime:
                    latest_mtime = mtime

        if latest_mtime is not None:
            return datetime.fromtimestamp(latest_mtime, tz=timezone.utc).isoformat()

        return None

    def discover_projects(self) -> list[DiscoveredProject]:
        """Discover all Edison projects in scan roots.

        Returns:
            List of discovered Edison projects with health metrics.
        """
        projects: list[DiscoveredProject] = []

        for scan_root in self.scan_roots:
            if not scan_root.exists():
                continue

            # Check if the scan root itself is an Edison project
            if self._is_edison_project(scan_root):
                project_id = self._generate_project_id(scan_root)
                projects.append(
                    DiscoveredProject(
                        project_id=project_id,
                        path=str(scan_root),
                        name=scan_root.name,
                        pinned=project_id in self._pinned_projects,
                        health=self._get_health(scan_root),
                        last_activity_at=self._get_last_activity(scan_root),
                        has_git=self._has_git(scan_root),
                    )
                )

            # Scan subdirectories (only one level deep for performance)
            for subdir in scan_root.iterdir():
                if not subdir.is_dir() or self._should_ignore(subdir):
                    continue

                if self._is_edison_project(subdir):
                    project_id = self._generate_project_id(subdir)
                    projects.append(
                        DiscoveredProject(
                            project_id=project_id,
                            path=str(subdir),
                            name=subdir.name,
                            pinned=project_id in self._pinned_projects,
                            health=self._get_health(subdir),
                            last_activity_at=self._get_last_activity(subdir),
                            has_git=self._has_git(subdir),
                        )
                    )

        return projects

    def get_project_by_id(self, project_id: str) -> DiscoveredProject | None:
        """Get a specific project by ID.

        Args:
            project_id: The project ID to look up.

        Returns:
            The discovered project or None if not found.
        """
        projects = self.discover_projects()
        for project in projects:
            if project.project_id == project_id:
                return project
        return None

    def set_pinned(self, project_id: str, pinned: bool) -> bool:
        """Set the pinned status for a project.

        Args:
            project_id: The project ID to update.
            pinned: Whether to pin or unpin.

        Returns:
            True if the project was found and updated, False otherwise.
        """
        # Verify the project exists
        project = self.get_project_by_id(project_id)
        if project is None:
            return False

        if pinned:
            self._pinned_projects.add(project_id)
        else:
            self._pinned_projects.discard(project_id)

        self._save_pinned_projects()
        return True

    def is_pinned(self, project_id: str) -> bool:
        """Check if a project is pinned."""
        return project_id in self._pinned_projects
