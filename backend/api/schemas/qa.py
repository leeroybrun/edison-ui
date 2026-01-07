"""QA-related Pydantic schemas (T030).

Implements schemas for QA listing and detail endpoints.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ValidationArtifact(BaseModel):
    """An artifact produced during validation."""

    name: str
    path: str  # Relative path or redacted path
    size_bytes: int | None = Field(None, alias="sizeBytes")

    model_config = {"populate_by_name": True}


class ValidatorDetail(BaseModel):
    """Details about a specific validator in a round."""

    validator_id: str = Field(..., alias="validatorId")
    verdict: str
    reason: str | None = None
    timestamp: str | None = None

    model_config = {"populate_by_name": True}


class ValidationRound(BaseModel):
    """A single round of validation."""

    round_number: int = Field(..., alias="roundNumber")
    timestamp: str
    verdict: str
    validators: list[ValidatorDetail] = Field(default_factory=list)
    artifacts: list[ValidationArtifact] = Field(default_factory=list)
    command_output: str | None = Field(None, alias="commandOutput")

    model_config = {"populate_by_name": True}


class QARecord(BaseModel):
    """A QA record summary."""

    qa_id: str = Field(..., alias="qaId")
    task_id: str = Field(..., alias="taskId")
    state: str
    verdict: str | None = None
    session_id: str | None = Field(None, alias="sessionId")
    round: int | None = None
    validators: list[str] = Field(default_factory=list)
    created_at: str = Field(..., alias="createdAt")
    updated_at: str = Field(..., alias="updatedAt")

    model_config = {"populate_by_name": True}


class QADetail(QARecord):
    """Detailed QA record with evidence rounds."""

    rounds: list[ValidationRound] = Field(default_factory=list)


class QAListResponse(BaseModel):
    """Response for list QA endpoints."""

    items: list[QARecord]
    total: int
    limit: int
    offset: int
