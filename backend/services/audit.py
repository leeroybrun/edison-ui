"""Audit writer service with filesystem confinement and redaction.

AuditWriter provides append-only JSONL audit logging with:
- Filesystem confinement to project's .project/logs/edison/ directory
- Automatic redaction of secrets, external paths, and env var values
- Thread-safe writes via file locking
"""

from __future__ import annotations

import fcntl
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from models.audit import AuditEntry


class FilesystemConfinementError(Exception):
    """Raised when an operation would violate filesystem confinement."""

    pass


# Patterns for detecting secrets
SECRET_PATTERNS: list[re.Pattern[str]] = [
    # OpenAI, Anthropic, etc. API keys
    re.compile(r"^sk-[a-zA-Z0-9]{20,}$"),
    # GitHub tokens
    re.compile(r"^ghp_[a-zA-Z0-9]{36,}$"),
    re.compile(r"^gho_[a-zA-Z0-9]{36,}$"),
    re.compile(r"^ghu_[a-zA-Z0-9]{36,}$"),
    re.compile(r"^ghs_[a-zA-Z0-9]{36,}$"),
    re.compile(r"^ghr_[a-zA-Z0-9]{36,}$"),
    # AWS access keys
    re.compile(r"^AKIA[0-9A-Z]{16}$"),
    # Generic long secrets (AWS secret keys, etc.)
    re.compile(r"^[a-zA-Z0-9/+=]{40,}$"),
    # Keys ending in common secret patterns
    re.compile(r".*(?:key|token|secret|password|credential).*", re.IGNORECASE),
]

# Keys that indicate the value should be treated as containing env vars
ENV_VAR_KEYS: set[str] = {"env", "environment", "env_vars", "envvars"}


def _is_secret_value(value: str) -> bool:
    """Check if a string value looks like a secret."""
    if not isinstance(value, str) or len(value) < 10:
        return False

    for pattern in SECRET_PATTERNS:
        if pattern.match(value):
            return True

    return False


def _is_external_path(value: str, project_root: str) -> bool:
    """Check if a string value is an absolute path outside project root."""
    if not isinstance(value, str):
        return False

    # Check if it looks like an absolute path
    if not value.startswith("/"):
        return False

    # Resolve both paths to handle symlinks and .. components
    try:
        resolved_value = Path(value).resolve()
        resolved_root = Path(project_root).resolve()
        # Check if the path is outside project root
        try:
            resolved_value.relative_to(resolved_root)
            return False  # Path is inside project root
        except ValueError:
            return True  # Path is outside project root
    except (OSError, ValueError):
        # If we can't resolve, treat it as external for safety
        return True


def _is_secret_key(key: str) -> bool:
    """Check if a key name suggests it contains a secret value."""
    secret_key_patterns = [
        "api_key",
        "apikey",
        "api-key",
        "secret",
        "token",
        "password",
        "credential",
        "private_key",
        "privatekey",
        "access_key",
        "accesskey",
    ]
    key_lower = key.lower()
    return any(pattern in key_lower for pattern in secret_key_patterns)


def redact_context(context: dict[str, Any], project_root: str) -> dict[str, Any]:
    """Redact sensitive values from a context dictionary.

    Redacts:
    - Absolute paths outside project root (replaced with [REDACTED_PATH])
    - Environment variable values (keys preserved, values become [REDACTED_ENV])
    - Known secret patterns (API keys, tokens) (replaced with [REDACTED_SECRET])

    Args:
        context: The context dictionary to redact.
        project_root: The project root path for path validation.

    Returns:
        A new dictionary with sensitive values redacted.
    """
    if not context:
        return {}

    def _redact_value(key: str, value: Any, is_env_context: bool = False) -> Any:
        """Recursively redact a value based on its content and context."""
        if value is None:
            return None

        if isinstance(value, dict):
            # Check if this is an env var dictionary
            key_lower = key.lower() if key else ""
            is_env = key_lower in ENV_VAR_KEYS or is_env_context

            return {
                k: _redact_value(k, v, is_env_context=is_env) for k, v in value.items()
            }

        if isinstance(value, list):
            return [_redact_value("", item, is_env_context) for item in value]

        if isinstance(value, str):
            # If we're in an env context, redact all string values
            if is_env_context:
                return "[REDACTED_ENV]"

            # Check if key suggests a secret
            if key and _is_secret_key(key):
                return "[REDACTED_SECRET]"

            # Check if value looks like a secret
            if _is_secret_value(value):
                return "[REDACTED_SECRET]"

            # Check if it's an external path
            if _is_external_path(value, project_root):
                return "[REDACTED_PATH]"

        # Return non-string, non-dict, non-list values as-is
        return value

    return {k: _redact_value(k, v) for k, v in context.items()}


class AuditWriter:
    """Append-only JSONL audit log writer with filesystem confinement.

    Writes audit entries to .project/logs/edison/ directory within a project root.
    All writes are thread-safe via file locking.

    Attributes:
        project_root: The project root directory.
        log_dir: The log directory (.project/logs/edison/).
    """

    def __init__(
        self,
        project_root: Path | str,
        log_dir_override: Path | str | None = None,
    ) -> None:
        """Initialize the audit writer.

        Args:
            project_root: The project root directory.
            log_dir_override: Optional override for log directory (for testing).
                Must still be within project root.

        Raises:
            FilesystemConfinementError: If log_dir_override is outside project root
                or if .project/logs/edison is a symlink escaping project root.
        """
        self._project_root = Path(project_root).resolve()

        if log_dir_override is not None:
            self._log_dir = Path(log_dir_override).resolve()
            self._validate_confinement(self._log_dir)
        else:
            self._log_dir = self._project_root / ".project" / "logs" / "edison"

            # Check if the path exists and is a symlink escaping project root
            if self._log_dir.exists() or self._log_dir.is_symlink():
                try:
                    resolved = self._log_dir.resolve()
                    self._validate_confinement(resolved)
                except OSError as e:
                    raise FilesystemConfinementError(
                        f"Cannot resolve log directory: {e}"
                    ) from e

        # Create the directory if it doesn't exist
        self._log_dir.mkdir(parents=True, exist_ok=True)

    def _validate_confinement(self, path: Path) -> None:
        """Validate that a path is within the project root.

        Args:
            path: The path to validate (must be resolved).

        Raises:
            FilesystemConfinementError: If path is outside project root.
        """
        try:
            path.relative_to(self._project_root)
        except ValueError as e:
            raise FilesystemConfinementError(
                f"Path {path} is outside project root {self._project_root}"
            ) from e

    @property
    def log_dir(self) -> Path:
        """Return the log directory path."""
        return self._log_dir

    def _get_log_file_path(self) -> Path:
        """Get the log file path for today's date.

        Returns:
            Path to the audit log file for today (audit-YYYY-MM-DD.jsonl).
        """
        today = date.today().isoformat()
        return self._log_dir / f"audit-{today}.jsonl"

    def write_entry(self, entry: AuditEntry) -> None:
        """Write an audit entry to the log file.

        The entry is serialized to JSON and appended as a single line.
        If the entry has a context, it is redacted before writing.

        Args:
            entry: The audit entry to write.
        """
        # Prepare the entry data
        entry_dict = entry.model_dump(mode="json")

        # Redact context if present
        if entry_dict.get("context") is not None:
            entry_dict["context"] = redact_context(
                entry_dict["context"],
                str(self._project_root),
            )

        # Serialize to JSON (single line)
        json_line = json.dumps(entry_dict, separators=(",", ":")) + "\n"

        # Write with file locking for thread safety
        log_file = self._get_log_file_path()

        with open(log_file, "a", encoding="utf-8") as f:
            # Acquire exclusive lock
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.write(json_line)
                f.flush()
            finally:
                # Release lock
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
