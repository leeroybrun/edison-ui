"""Search service (T074).

Provides text-based search across tasks, sessions, QA, and memory scopes.
Uses simple text matching with relevance scoring.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SearchMatch:
    """A search match with score and context."""

    entity_id: str
    entity_type: str
    title: str | None
    snippet: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class SearchService:
    """Service for searching across Edison project entities."""

    # Maximum snippet length
    MAX_SNIPPET_LENGTH = 200

    # Score weights
    TITLE_MATCH_WEIGHT = 1.0
    BODY_MATCH_WEIGHT = 0.6
    ID_MATCH_WEIGHT = 0.3

    def __init__(self, project_path: str) -> None:
        """Initialize the search service.

        Args:
            project_path: Absolute path to the Edison project root.
        """
        self.project_path = Path(project_path)
        self.project_dir = self.project_path / ".project"

    def _normalize_query(self, query: str) -> str:
        """Normalize search query for matching."""
        return query.lower().strip()

    def _calculate_score(
        self,
        query: str,
        text: str,
        is_title: bool = False,
        is_id: bool = False,
    ) -> float:
        """Calculate relevance score for a text match.

        Args:
            query: Normalized search query.
            text: Text to search in.
            is_title: Whether this is a title field (higher weight).
            is_id: Whether this is an ID field.

        Returns:
            Score between 0 and 1.
        """
        if not text:
            return 0.0

        text_lower = text.lower()
        query_lower = query.lower()

        # No match
        if query_lower not in text_lower:
            return 0.0

        # Base score based on field type
        if is_id:
            base_score = self.ID_MATCH_WEIGHT
        elif is_title:
            base_score = self.TITLE_MATCH_WEIGHT
        else:
            base_score = self.BODY_MATCH_WEIGHT

        # Boost for exact word match
        words = re.findall(r"\b\w+\b", text_lower)
        if query_lower in words:
            base_score = min(1.0, base_score * 1.2)

        # Boost for match at start
        if text_lower.startswith(query_lower):
            base_score = min(1.0, base_score * 1.1)

        return min(1.0, base_score)

    def _extract_snippet(self, text: str, query: str) -> str:
        """Extract a snippet containing the query match.

        Args:
            text: Full text to extract from.
            query: Search query to find.

        Returns:
            Snippet containing the match with context.
        """
        if not text:
            return ""

        text_lower = text.lower()
        query_lower = query.lower()

        # Find match position
        pos = text_lower.find(query_lower)
        if pos == -1:
            # No match, return beginning of text
            return text[: self.MAX_SNIPPET_LENGTH] + ("..." if len(text) > self.MAX_SNIPPET_LENGTH else "")

        # Extract context around match
        start = max(0, pos - 50)
        end = min(len(text), pos + len(query) + 150)

        snippet = text[start:end]

        # Add ellipsis if truncated
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."

        # Clean up whitespace
        snippet = " ".join(snippet.split())

        return snippet[: self.MAX_SNIPPET_LENGTH]

    def _parse_frontmatter(self, content: str) -> dict[str, Any]:
        """Parse YAML frontmatter from a markdown file."""
        result: dict[str, Any] = {}
        match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if not match:
            return result

        frontmatter = match.group(1)
        try:
            import yaml

            loaded = yaml.safe_load(frontmatter)
        except Exception:
            return result

        if not isinstance(loaded, dict):
            return result

        return dict(loaded)

    def _get_body_content(self, content: str) -> str:
        """Extract body content after frontmatter."""
        match = re.match(r"^---\s*\n.*?\n---\s*\n?(.*)", content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return content.strip()

    def search_tasks(
        self, query: str, limit: int = 20
    ) -> list[SearchMatch]:
        """Search tasks by title and body content.

        Args:
            query: Search query.
            limit: Maximum results to return.

        Returns:
            List of matching tasks sorted by score.
        """
        results: list[SearchMatch] = []
        query_normalized = self._normalize_query(query)

        if not query_normalized:
            return results

        tasks_dir = self.project_dir / "tasks"
        if not tasks_dir.exists():
            return results

        # Scan all task states
        for state_dir in tasks_dir.iterdir():
            if not state_dir.is_dir():
                continue

            for task_file in state_dir.glob("*.md"):
                try:
                    content = task_file.read_text(encoding="utf-8")
                except OSError:
                    continue

                fm = self._parse_frontmatter(content)
                task_id = fm.get("id", task_file.stem)
                title = fm.get("title", task_id)
                body = self._get_body_content(content)

                # Calculate scores for different fields
                title_score = self._calculate_score(query_normalized, str(title), is_title=True)
                body_score = self._calculate_score(query_normalized, body)
                id_score = self._calculate_score(query_normalized, str(task_id), is_id=True)

                # Use highest score
                best_score = max(title_score, body_score, id_score)

                if best_score > 0:
                    # Determine snippet source
                    if title_score >= body_score:
                        snippet = self._extract_snippet(str(title), query_normalized)
                    else:
                        snippet = self._extract_snippet(body, query_normalized)

                    results.append(
                        SearchMatch(
                            entity_id=str(task_id),
                            entity_type="task",
                            title=str(title),
                            snippet=snippet,
                            score=best_score,
                            metadata={"state": state_dir.name},
                        )
                    )

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    def search_sessions(
        self, query: str, limit: int = 20
    ) -> list[SearchMatch]:
        """Search sessions by ID and activity log.

        Args:
            query: Search query.
            limit: Maximum results to return.

        Returns:
            List of matching sessions sorted by score.
        """
        results: list[SearchMatch] = []
        query_normalized = self._normalize_query(query)

        if not query_normalized:
            return results

        sessions_dir = self.project_dir / "sessions"
        if not sessions_dir.exists():
            return results

        # Scan all session states
        for state_dir in sessions_dir.iterdir():
            if not state_dir.is_dir():
                continue

            for session_dir in state_dir.iterdir():
                if not session_dir.is_dir():
                    continue

                session_file = session_dir / "session.json"
                if not session_file.exists():
                    continue

                try:
                    with open(session_file) as f:
                        data = json.load(f)
                except (json.JSONDecodeError, OSError):
                    continue

                session_id = data.get("id", "")
                if not session_id:
                    continue

                # Search in session ID
                id_score = self._calculate_score(query_normalized, session_id, is_id=True)

                # Search in activity log
                activity = data.get("activity", [])
                activity_text = ""
                for entry in activity:
                    if isinstance(entry, dict):
                        msg = entry.get("message", "")
                        if msg:
                            activity_text += f" {msg}"

                activity_score = self._calculate_score(query_normalized, activity_text)

                # Search in owner
                owner = data.get("meta", {}).get("owner", "")
                owner_score = self._calculate_score(query_normalized, owner)

                best_score = max(id_score, activity_score, owner_score)

                if best_score > 0:
                    # Determine snippet
                    if id_score >= activity_score:
                        snippet = f"Session: {session_id}"
                    else:
                        snippet = self._extract_snippet(activity_text.strip(), query_normalized)

                    results.append(
                        SearchMatch(
                            entity_id=session_id,
                            entity_type="session",
                            title=None,
                            snippet=snippet,
                            score=best_score,
                            metadata={"state": state_dir.name},
                        )
                    )

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    def search_qa(
        self, query: str, limit: int = 20
    ) -> list[SearchMatch]:
        """Search QA records by ID, linked task, and content.

        Args:
            query: Search query.
            limit: Maximum results to return.

        Returns:
            List of matching QA records sorted by score.
        """
        results: list[SearchMatch] = []
        query_normalized = self._normalize_query(query)

        if not query_normalized:
            return results

        qa_dir = self.project_dir / "qa"
        if not qa_dir.exists():
            return results

        # Scan all QA states
        for state_dir in qa_dir.iterdir():
            if not state_dir.is_dir() or state_dir.name == "validation-evidence":
                continue

            for qa_file in state_dir.glob("*.md"):
                try:
                    content = qa_file.read_text(encoding="utf-8")
                except OSError:
                    continue

                fm = self._parse_frontmatter(content)
                qa_id = fm.get("id", qa_file.stem)
                task_id = fm.get("task_id", "")
                body = self._get_body_content(content)

                # Calculate scores
                id_score = self._calculate_score(query_normalized, str(qa_id), is_id=True)
                task_score = self._calculate_score(query_normalized, str(task_id), is_id=True)
                body_score = self._calculate_score(query_normalized, body)

                best_score = max(id_score, task_score, body_score)

                if best_score > 0:
                    snippet = self._extract_snippet(body, query_normalized) if body else f"QA for {task_id}"

                    results.append(
                        SearchMatch(
                            entity_id=str(qa_id),
                            entity_type="qa",
                            title=None,
                            snippet=snippet,
                            score=best_score,
                            metadata={"task_id": str(task_id), "state": state_dir.name},
                        )
                    )

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    def search_memory(
        self, query: str, limit: int = 20
    ) -> list[SearchMatch]:
        """Search memory scope.

        Currently returns empty list as memory is not configured.

        Args:
            query: Search query.
            limit: Maximum results to return.

        Returns:
            Empty list (memory not configured).
        """
        # Memory search is deferred - return empty array
        return []

    def search_all(
        self,
        query: str,
        scopes: list[str] | None = None,
        limit: int = 20,
    ) -> dict[str, list[SearchMatch]]:
        """Search across all or specified scopes.

        Args:
            query: Search query.
            scopes: List of scopes to search (tasks, sessions, qa, memory).
                   If None, searches all scopes.
            limit: Maximum results per scope.

        Returns:
            Dictionary mapping scope names to search results.
        """
        all_scopes = {"tasks", "sessions", "qa", "memory"}

        if scopes is None:
            active_scopes = all_scopes
        else:
            active_scopes = set(scopes) & all_scopes

        results: dict[str, list[SearchMatch]] = {
            "tasks": [],
            "sessions": [],
            "qa": [],
            "memory": [],
        }

        if "tasks" in active_scopes:
            results["tasks"] = self.search_tasks(query, limit)

        if "sessions" in active_scopes:
            results["sessions"] = self.search_sessions(query, limit)

        if "qa" in active_scopes:
            results["qa"] = self.search_qa(query, limit)

        if "memory" in active_scopes:
            results["memory"] = self.search_memory(query, limit)

        return results
