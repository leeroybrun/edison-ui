"""QA reader service (T030)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from api.schemas.qa import QADetail, QARecord, ValidationArtifact, ValidationRound


@dataclass
class QAData:
    """Parsed QA data from filesystem."""

    qa_id: str
    task_id: str
    state: str
    verdict: str | None
    session_id: str | None
    round: int | None
    validators: list[str]
    created_at: str
    updated_at: str
    file_path: str


class QAReaderService:
    """Service for reading QA records and evidence."""

    def __init__(self, project_path: str) -> None:
        """Initialize the QA reader service."""
        self.project_path = Path(project_path)
        self.project_dir = self.project_path / ".project"
        self.qa_dir = self.project_dir / "qa"
        self._qa_cache: list[QAData] | None = None

    def _parse_frontmatter(self, content: str) -> dict[str, Any]:
        """Parse YAML frontmatter (simplified version)."""
        result: dict[str, Any] = {}
        match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if not match:
            return result

        frontmatter = match.group(1)

        # Simple parser for list items and keys
        lines = frontmatter.split("\n")
        current_key: str | None = None
        current_list: list[str] | None = None

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # List item
            if stripped.startswith("- ") and current_key:
                if current_list is None:
                    current_list = []
                val = stripped[2:].strip().strip("'\"")
                current_list.append(val)
                result[current_key] = current_list
                continue

            # Key-value
            if ":" in line:
                if current_list is not None:
                    current_list = None

                parts = line.split(":", 1)
                key = parts[0].strip()
                val = parts[1].strip()

                current_key = key
                if val:
                    result[key] = val.strip("'\"")
                else:
                    # Could be start of a list
                    pass

        return result

    def _parse_qa_file(self, file_path: Path, state: str) -> QAData | None:
        """Parse a QA markdown file."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError:
            return None

        fm = self._parse_frontmatter(content)

        qa_id = str(fm.get("id", file_path.stem))
        task_id = str(fm.get("task_id", ""))
        # Fallback if task_id not in frontmatter, try to parse from filename: {task-id}-qa.md
        if not task_id and file_path.name.endswith("-qa.md"):
            task_id = file_path.name.replace("-qa.md", "")

        if not task_id:
            return None

        round_val = fm.get("round")
        try:
            round_num = int(round_val) if round_val is not None else None
        except ValueError:
            round_num = None

        validators_raw = fm.get("validators", [])
        validators = validators_raw if isinstance(validators_raw, list) else []

        verdict = str(fm.get("verdict")) if fm.get("verdict") else None

        # Fallback: Check evidence if verdict is missing
        if not verdict and round_num is not None:
            evidence_dir = (
                self.qa_dir / "validation-evidence" / task_id / f"round-{round_num}"
            )
            summary_file = evidence_dir / "bundle-summary.md"
            if summary_file.exists():
                try:
                    summary_content = summary_file.read_text(encoding="utf-8").lower()
                    if "failed" in summary_content:
                        verdict = "failed"
                    elif "passed" in summary_content:
                        verdict = "passed"
                except OSError:
                    pass

        return QAData(
            qa_id=qa_id,
            task_id=task_id,
            state=state,
            verdict=verdict,
            session_id=str(fm.get("session_id")) if fm.get("session_id") else None,
            round=round_num,
            validators=validators,
            created_at=str(fm.get("created_at", "1970-01-01T00:00:00Z")),
            updated_at=str(fm.get("updated_at", "1970-01-01T00:00:00Z")),
            file_path=str(file_path),
        )

    def _load_all_qa(self) -> list[QAData]:
        """Load all QA records."""
        if self._qa_cache is not None:
            return self._qa_cache

        records: list[QAData] = []
        if not self.qa_dir.exists():
            return records

        for state in ["waiting", "todo", "wip", "done", "validated"]:
            state_dir = self.qa_dir / state
            if not state_dir.exists():
                continue

            for qa_file in state_dir.glob("*.md"):
                record = self._parse_qa_file(qa_file, state)
                if record:
                    records.append(record)

        self._qa_cache = records
        return records

    def list_qa_records(
        self,
        session_id: str | None = None,
        state: str | None = None,
        verdict: str | None = None,
    ) -> list[QARecord]:
        """List filtered QA records."""
        all_records = self._load_all_qa()
        filtered = []

        for r in all_records:
            if session_id and r.session_id != session_id:
                continue
            if state and r.state != state:
                continue
            if verdict and r.verdict != verdict:
                continue

            filtered.append(
                QARecord(
                    qa_id=r.qa_id,
                    task_id=r.task_id,
                    state=r.state,
                    verdict=r.verdict,
                    session_id=r.session_id,
                    round=r.round,
                    validators=r.validators,
                    created_at=r.created_at,
                    updated_at=r.updated_at,
                )
            )

        return filtered

    def get_qa_detail(self, task_id: str) -> QADetail | None:
        """Get QA detail with evidence for a task."""
        all_records = self._load_all_qa()
        record = next((r for r in all_records if r.task_id == task_id), None)
        if not record:
            return None

        # Load evidence rounds
        rounds: list[ValidationRound] = []
        evidence_root = self.qa_dir / "validation-evidence" / task_id

        if evidence_root.exists():
            for round_dir in evidence_root.glob("round-*"):
                try:
                    round_num = int(round_dir.name.split("-")[1])
                except (IndexError, ValueError):
                    continue

                artifacts: list[ValidationArtifact] = []
                for artifact_file in round_dir.iterdir():
                    if artifact_file.is_file():
                        artifacts.append(
                            ValidationArtifact(
                                name=artifact_file.name,
                                path=f"qa/validation-evidence/{task_id}/{round_dir.name}/{artifact_file.name}",
                                size_bytes=artifact_file.stat().st_size,
                            )
                        )

                rounds.append(
                    ValidationRound(
                        round_number=round_num,
                        timestamp=record.updated_at,  # Approximate
                        verdict=record.verdict or "pending",
                        validators=[],  # Would parse from round summary if available
                        artifacts=artifacts,
                    )
                )

        rounds.sort(key=lambda x: x.round_number)

        return QADetail(
            qa_id=record.qa_id,
            task_id=record.task_id,
            state=record.state,
            verdict=record.verdict,
            session_id=record.session_id,
            created_at=record.created_at,
            updated_at=record.updated_at,
            rounds=rounds,
        )
