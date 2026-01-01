"""Tests for API schemas (errors and guards).

TDD RED Phase: These tests describe the expected behavior of the schema models.
"""
from __future__ import annotations

from typing import Any



class TestErrorDetail:
    """Tests for ErrorDetail schema."""

    def test_error_detail_with_all_fields(self) -> None:
        """ErrorDetail should accept code, message, and optional field."""
        from api.schemas.errors import ErrorDetail

        detail = ErrorDetail(
            code="VALIDATION_ERROR",
            message="Invalid input provided",
            field="email",
        )
        assert detail.code == "VALIDATION_ERROR"
        assert detail.message == "Invalid input provided"
        assert detail.field == "email"

    def test_error_detail_without_field(self) -> None:
        """ErrorDetail should work without optional field."""
        from api.schemas.errors import ErrorDetail

        detail = ErrorDetail(
            code="INTERNAL_ERROR",
            message="An internal error occurred",
        )
        assert detail.code == "INTERNAL_ERROR"
        assert detail.message == "An internal error occurred"
        assert detail.field is None

    def test_error_detail_serialization(self) -> None:
        """ErrorDetail should serialize to JSON correctly."""
        from api.schemas.errors import ErrorDetail

        detail = ErrorDetail(
            code="NOT_FOUND",
            message="Resource not found",
            field="task_id",
        )
        json_data = detail.model_dump()
        assert json_data == {
            "code": "NOT_FOUND",
            "message": "Resource not found",
            "field": "task_id",
        }

    def test_error_detail_serialization_without_field(self) -> None:
        """ErrorDetail without field should serialize with field=None."""
        from api.schemas.errors import ErrorDetail

        detail = ErrorDetail(
            code="UNAUTHORIZED",
            message="Authentication required",
        )
        json_data = detail.model_dump()
        assert json_data == {
            "code": "UNAUTHORIZED",
            "message": "Authentication required",
            "field": None,
        }

    def test_error_detail_from_dict(self) -> None:
        """ErrorDetail should be constructible from dict."""
        from api.schemas.errors import ErrorDetail

        data = {
            "code": "BAD_REQUEST",
            "message": "Malformed request",
            "field": "body",
        }
        detail = ErrorDetail.model_validate(data)
        assert detail.code == "BAD_REQUEST"
        assert detail.message == "Malformed request"
        assert detail.field == "body"


class TestErrorResponse:
    """Tests for ErrorResponse schema."""

    def test_error_response_with_request_id(self) -> None:
        """ErrorResponse should include error detail and request_id."""
        from api.schemas.errors import ErrorDetail, ErrorResponse

        error = ErrorDetail(code="NOT_FOUND", message="Task not found")
        response = ErrorResponse(error=error, request_id="req-12345")
        assert response.error.code == "NOT_FOUND"
        assert response.error.message == "Task not found"
        assert response.request_id == "req-12345"

    def test_error_response_without_request_id(self) -> None:
        """ErrorResponse should work without request_id."""
        from api.schemas.errors import ErrorDetail, ErrorResponse

        error = ErrorDetail(code="FORBIDDEN", message="Access denied")
        response = ErrorResponse(error=error)
        assert response.error.code == "FORBIDDEN"
        assert response.request_id is None

    def test_error_response_serialization(self) -> None:
        """ErrorResponse should serialize correctly with nested ErrorDetail."""
        from api.schemas.errors import ErrorDetail, ErrorResponse

        error = ErrorDetail(
            code="GUARD_BLOCKED",
            message="Task state does not allow this action",
            field="status",
        )
        response = ErrorResponse(error=error, request_id="req-abc123")
        json_data = response.model_dump()
        assert json_data == {
            "error": {
                "code": "GUARD_BLOCKED",
                "message": "Task state does not allow this action",
                "field": "status",
            },
            "request_id": "req-abc123",
        }


class TestValidationErrorResponse:
    """Tests for ValidationErrorResponse schema."""

    def test_validation_error_response_with_multiple_errors(self) -> None:
        """ValidationErrorResponse should contain list of ErrorDetail."""
        from api.schemas.errors import ErrorDetail, ValidationErrorResponse

        errors = [
            ErrorDetail(code="REQUIRED", message="Field is required", field="name"),
            ErrorDetail(code="INVALID_FORMAT", message="Invalid email", field="email"),
        ]
        response = ValidationErrorResponse(errors=errors, request_id="req-xyz")
        assert len(response.errors) == 2
        assert response.errors[0].field == "name"
        assert response.errors[1].field == "email"
        assert response.request_id == "req-xyz"

    def test_validation_error_response_without_request_id(self) -> None:
        """ValidationErrorResponse should work without request_id."""
        from api.schemas.errors import ErrorDetail, ValidationErrorResponse

        errors = [ErrorDetail(code="TOO_LONG", message="Value too long", field="title")]
        response = ValidationErrorResponse(errors=errors)
        assert len(response.errors) == 1
        assert response.request_id is None

    def test_validation_error_response_serialization(self) -> None:
        """ValidationErrorResponse should serialize correctly."""
        from api.schemas.errors import ErrorDetail, ValidationErrorResponse

        errors = [
            ErrorDetail(code="MIN_LENGTH", message="Too short", field="password"),
            ErrorDetail(code="PATTERN", message="Invalid pattern", field="username"),
        ]
        response = ValidationErrorResponse(errors=errors, request_id="req-val123")
        json_data = response.model_dump()
        assert json_data == {
            "errors": [
                {"code": "MIN_LENGTH", "message": "Too short", "field": "password"},
                {"code": "PATTERN", "message": "Invalid pattern", "field": "username"},
            ],
            "request_id": "req-val123",
        }

    def test_validation_error_response_empty_errors(self) -> None:
        """ValidationErrorResponse should accept empty errors list."""
        from api.schemas.errors import ValidationErrorResponse

        response = ValidationErrorResponse(errors=[])
        assert response.errors == []


class TestGuardCheckResult:
    """Tests for GuardCheckResult schema."""

    def test_guard_check_result_allowed(self) -> None:
        """GuardCheckResult with allowed=True."""
        from api.schemas.guards import GuardCheckResult

        result = GuardCheckResult(
            allowed=True,
            guard_name="status_check",
        )
        assert result.allowed is True
        assert result.guard_name == "status_check"
        assert result.reason is None
        assert result.required_state is None
        assert result.current_state is None

    def test_guard_check_result_blocked(self) -> None:
        """GuardCheckResult with allowed=False should include reason and states."""
        from api.schemas.guards import GuardCheckResult

        result = GuardCheckResult(
            allowed=False,
            guard_name="qa_validation_guard",
            reason="Task must be validated before promotion",
            required_state="validated",
            current_state="pending",
        )
        assert result.allowed is False
        assert result.guard_name == "qa_validation_guard"
        assert result.reason == "Task must be validated before promotion"
        assert result.required_state == "validated"
        assert result.current_state == "pending"

    def test_guard_check_result_serialization_allowed(self) -> None:
        """GuardCheckResult (allowed) should serialize correctly."""
        from api.schemas.guards import GuardCheckResult

        result = GuardCheckResult(allowed=True, guard_name="actor_check")
        json_data = result.model_dump()
        assert json_data == {
            "allowed": True,
            "guard_name": "actor_check",
            "reason": None,
            "required_state": None,
            "current_state": None,
        }

    def test_guard_check_result_serialization_blocked(self) -> None:
        """GuardCheckResult (blocked) should serialize correctly."""
        from api.schemas.guards import GuardCheckResult

        result = GuardCheckResult(
            allowed=False,
            guard_name="state_transition_guard",
            reason="Cannot move from wip to backlog",
            required_state="backlog,done",
            current_state="wip",
        )
        json_data = result.model_dump()
        assert json_data == {
            "allowed": False,
            "guard_name": "state_transition_guard",
            "reason": "Cannot move from wip to backlog",
            "required_state": "backlog,done",
            "current_state": "wip",
        }

    def test_guard_check_result_from_dict(self) -> None:
        """GuardCheckResult should be constructible from dict."""
        from api.schemas.guards import GuardCheckResult

        data = {
            "allowed": False,
            "guard_name": "permission_guard",
            "reason": "Insufficient permissions",
            "required_state": None,
            "current_state": None,
        }
        result = GuardCheckResult.model_validate(data)
        assert result.allowed is False
        assert result.guard_name == "permission_guard"


class TestGuardPreviewResponse:
    """Tests for GuardPreviewResponse schema."""

    def test_guard_preview_response_can_proceed(self) -> None:
        """GuardPreviewResponse with all checks passing."""
        from api.schemas.guards import GuardCheckResult, GuardPreviewResponse

        checks = [
            GuardCheckResult(allowed=True, guard_name="state_check"),
            GuardCheckResult(allowed=True, guard_name="actor_check"),
        ]
        response = GuardPreviewResponse(can_proceed=True, checks=checks)
        assert response.can_proceed is True
        assert len(response.checks) == 2
        assert response.warnings == []

    def test_guard_preview_response_blocked(self) -> None:
        """GuardPreviewResponse with some checks failing."""
        from api.schemas.guards import GuardCheckResult, GuardPreviewResponse

        checks = [
            GuardCheckResult(allowed=True, guard_name="state_check"),
            GuardCheckResult(
                allowed=False,
                guard_name="validation_check",
                reason="QA validation required",
                required_state="validated",
                current_state="pending",
            ),
        ]
        response = GuardPreviewResponse(can_proceed=False, checks=checks)
        assert response.can_proceed is False
        assert len(response.checks) == 2
        assert response.checks[1].allowed is False

    def test_guard_preview_response_with_warnings(self) -> None:
        """GuardPreviewResponse with non-blocking warnings."""
        from api.schemas.guards import GuardCheckResult, GuardPreviewResponse

        checks = [GuardCheckResult(allowed=True, guard_name="state_check")]
        warnings = [
            "Task has been in current state for >7 days",
            "No recent activity detected",
        ]
        response = GuardPreviewResponse(
            can_proceed=True,
            checks=checks,
            warnings=warnings,
        )
        assert response.can_proceed is True
        assert len(response.warnings) == 2
        assert "Task has been in current state for >7 days" in response.warnings

    def test_guard_preview_response_serialization(self) -> None:
        """GuardPreviewResponse should serialize correctly."""
        from api.schemas.guards import GuardCheckResult, GuardPreviewResponse

        checks = [
            GuardCheckResult(allowed=True, guard_name="check1"),
            GuardCheckResult(
                allowed=False,
                guard_name="check2",
                reason="Blocked",
                required_state="done",
                current_state="wip",
            ),
        ]
        response = GuardPreviewResponse(
            can_proceed=False,
            checks=checks,
            warnings=["Consider review"],
        )
        json_data = response.model_dump()
        assert json_data == {
            "can_proceed": False,
            "checks": [
                {
                    "allowed": True,
                    "guard_name": "check1",
                    "reason": None,
                    "required_state": None,
                    "current_state": None,
                },
                {
                    "allowed": False,
                    "guard_name": "check2",
                    "reason": "Blocked",
                    "required_state": "done",
                    "current_state": "wip",
                },
            ],
            "warnings": ["Consider review"],
        }

    def test_guard_preview_response_default_warnings(self) -> None:
        """GuardPreviewResponse should default to empty warnings list."""
        from api.schemas.guards import GuardCheckResult, GuardPreviewResponse

        checks = [GuardCheckResult(allowed=True, guard_name="check")]
        response = GuardPreviewResponse(can_proceed=True, checks=checks)
        assert response.warnings == []


class TestGuardApplyResponse:
    """Tests for GuardApplyResponse schema."""

    def test_guard_apply_response_success(self) -> None:
        """GuardApplyResponse for successful action."""
        from api.schemas.guards import GuardApplyResponse

        result: dict[str, Any] = {"new_status": "done", "updated_at": "2024-01-15T10:30:00Z"}
        response = GuardApplyResponse(
            success=True,
            result=result,
            audit_entry_id="audit-12345",
        )
        assert response.success is True
        assert response.result == result
        assert response.audit_entry_id == "audit-12345"

    def test_guard_apply_response_failure(self) -> None:
        """GuardApplyResponse for failed action."""
        from api.schemas.guards import GuardApplyResponse

        response = GuardApplyResponse(
            success=False,
            result=None,
            audit_entry_id="audit-67890",
        )
        assert response.success is False
        assert response.result is None
        assert response.audit_entry_id == "audit-67890"

    def test_guard_apply_response_without_audit(self) -> None:
        """GuardApplyResponse without audit_entry_id."""
        from api.schemas.guards import GuardApplyResponse

        response = GuardApplyResponse(
            success=True,
            result={"task_id": "T001"},
        )
        assert response.success is True
        assert response.audit_entry_id is None

    def test_guard_apply_response_serialization(self) -> None:
        """GuardApplyResponse should serialize correctly."""
        from api.schemas.guards import GuardApplyResponse

        response = GuardApplyResponse(
            success=True,
            result={"status": "completed", "metrics": {"duration": 120}},
            audit_entry_id="audit-abc",
        )
        json_data = response.model_dump()
        assert json_data == {
            "success": True,
            "result": {"status": "completed", "metrics": {"duration": 120}},
            "audit_entry_id": "audit-abc",
        }

    def test_guard_apply_response_complex_result(self) -> None:
        """GuardApplyResponse with complex nested result dict."""
        from api.schemas.guards import GuardApplyResponse

        complex_result: dict[str, Any] = {
            "task": {
                "id": "T001",
                "status": "done",
                "transitions": [
                    {"from": "wip", "to": "done", "timestamp": "2024-01-15"},
                ],
            },
            "warnings": [],
        }
        response = GuardApplyResponse(success=True, result=complex_result)
        assert response.result is not None
        assert response.result["task"]["id"] == "T001"


class TestSchemaExports:
    """Tests for schema module exports."""

    def test_errors_module_exports(self) -> None:
        """api.schemas.errors should export all error schemas."""
        from api.schemas import errors

        assert hasattr(errors, "ErrorDetail")
        assert hasattr(errors, "ErrorResponse")
        assert hasattr(errors, "ValidationErrorResponse")

    def test_guards_module_exports(self) -> None:
        """api.schemas.guards should export all guard schemas."""
        from api.schemas import guards

        assert hasattr(guards, "GuardCheckResult")
        assert hasattr(guards, "GuardPreviewResponse")
        assert hasattr(guards, "GuardApplyResponse")

    def test_schemas_init_exports(self) -> None:
        """api.schemas should export all schemas from __init__."""
        from api import schemas

        # Error schemas
        assert hasattr(schemas, "ErrorDetail")
        assert hasattr(schemas, "ErrorResponse")
        assert hasattr(schemas, "ValidationErrorResponse")
        # Guard schemas
        assert hasattr(schemas, "GuardCheckResult")
        assert hasattr(schemas, "GuardPreviewResponse")
        assert hasattr(schemas, "GuardApplyResponse")


class TestJsonSchemaGeneration:
    """Tests for JSON schema generation support."""

    def test_error_detail_json_schema(self) -> None:
        """ErrorDetail should generate valid JSON schema."""
        from api.schemas.errors import ErrorDetail

        schema = ErrorDetail.model_json_schema()
        assert "properties" in schema
        assert "code" in schema["properties"]
        assert "message" in schema["properties"]
        assert "field" in schema["properties"]

    def test_guard_check_result_json_schema(self) -> None:
        """GuardCheckResult should generate valid JSON schema."""
        from api.schemas.guards import GuardCheckResult

        schema = GuardCheckResult.model_json_schema()
        assert "properties" in schema
        assert "allowed" in schema["properties"]
        assert "guard_name" in schema["properties"]

    def test_guard_preview_response_json_schema(self) -> None:
        """GuardPreviewResponse should generate valid JSON schema with refs."""
        from api.schemas.guards import GuardPreviewResponse

        schema = GuardPreviewResponse.model_json_schema()
        assert "properties" in schema
        assert "can_proceed" in schema["properties"]
        assert "checks" in schema["properties"]
        assert "warnings" in schema["properties"]
