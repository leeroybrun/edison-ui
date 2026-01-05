"""Tests for actor identity and audit entry models.

TDD RED PHASE: These tests are written BEFORE implementation.
Expected: All tests should fail (module not found).
"""

from __future__ import annotations

import getpass
from datetime import datetime, timezone
from typing import Any


class TestActorIdentity:
    """Test ActorIdentity model."""

    def test_get_current_actor_returns_actor_identity_with_os_user(self) -> None:
        """get_current_actor() should return ActorIdentity with os_user populated."""
        from models.actor import ActorIdentity, get_current_actor

        actor = get_current_actor()

        assert isinstance(actor, ActorIdentity)
        assert actor.os_user == getpass.getuser()

    def test_get_current_actor_has_none_display_name_by_default(self) -> None:
        """get_current_actor() should return None for display_name by default."""
        from models.actor import get_current_actor

        actor = get_current_actor()

        assert actor.display_name is None

    def test_actor_identity_accepts_display_name(self) -> None:
        """ActorIdentity can be created with a display_name."""
        from models.actor import ActorIdentity

        actor = ActorIdentity(os_user="testuser", display_name="Test User")

        assert actor.os_user == "testuser"
        assert actor.display_name == "Test User"

    def test_actor_identity_serializes_to_dict(self) -> None:
        """ActorIdentity should serialize to dict via model_dump."""
        from models.actor import ActorIdentity

        actor = ActorIdentity(os_user="testuser", display_name="Test User")
        data = actor.model_dump()

        assert data == {"os_user": "testuser", "display_name": "Test User"}

    def test_actor_identity_serializes_to_json(self) -> None:
        """ActorIdentity should serialize to JSON."""
        from models.actor import ActorIdentity

        actor = ActorIdentity(os_user="testuser", display_name=None)
        json_str = actor.model_dump_json()

        assert '"os_user":"testuser"' in json_str
        assert '"display_name":null' in json_str


class TestAuditTarget:
    """Test AuditTarget model."""

    def test_audit_target_has_entity_type_and_entity_id(self) -> None:
        """AuditTarget must have entity_type and entity_id fields."""
        from models.audit import AuditTarget

        target = AuditTarget(entity_type="task", entity_id="T001")

        assert target.entity_type == "task"
        assert target.entity_id == "T001"

    def test_audit_target_serializes_to_dict(self) -> None:
        """AuditTarget should serialize to dict."""
        from models.audit import AuditTarget

        target = AuditTarget(entity_type="session", entity_id="S001")
        data = target.model_dump()

        assert data == {"entity_type": "session", "entity_id": "S001"}


class TestAuditEntry:
    """Test AuditEntry model."""

    def test_audit_entry_creation_with_all_fields(self) -> None:
        """AuditEntry can be created with all required fields."""
        from models.actor import ActorIdentity
        from models.audit import AuditEntry, AuditTarget

        actor = ActorIdentity(os_user="testuser", display_name=None)
        target = AuditTarget(entity_type="task", entity_id="T001")
        timestamp = datetime.now(timezone.utc)

        entry = AuditEntry(
            action_id="ACT001",
            actor=actor,
            timestamp=timestamp,
            action_type="task_claimed",
            target=target,
            outcome="success",
            context=None,
        )

        assert entry.action_id == "ACT001"
        assert entry.actor == actor
        assert entry.timestamp == timestamp
        assert entry.action_type == "task_claimed"
        assert entry.target == target
        assert entry.outcome == "success"
        assert entry.context is None

    def test_audit_entry_with_context_dict(self) -> None:
        """AuditEntry can include optional context dict."""
        from models.actor import ActorIdentity
        from models.audit import AuditEntry, AuditTarget

        actor = ActorIdentity(os_user="testuser", display_name=None)
        target = AuditTarget(entity_type="task", entity_id="T001")
        timestamp = datetime.now(timezone.utc)
        context: dict[str, Any] = {"previous_status": "todo", "new_status": "wip"}

        entry = AuditEntry(
            action_id="ACT002",
            actor=actor,
            timestamp=timestamp,
            action_type="task_status_changed",
            target=target,
            outcome="success",
            context=context,
        )

        assert entry.context == context
        assert entry.context["previous_status"] == "todo"
        assert entry.context["new_status"] == "wip"

    def test_audit_entry_serializes_with_nested_models(self) -> None:
        """AuditEntry should serialize including nested ActorIdentity and AuditTarget."""
        from models.actor import ActorIdentity
        from models.audit import AuditEntry, AuditTarget

        actor = ActorIdentity(os_user="testuser", display_name="Test User")
        target = AuditTarget(entity_type="qa", entity_id="QA001")
        timestamp = datetime(2025, 12, 27, 12, 0, 0, tzinfo=timezone.utc)

        entry = AuditEntry(
            action_id="ACT003",
            actor=actor,
            timestamp=timestamp,
            action_type="qa_validated",
            target=target,
            outcome="success",
            context={"validator": "human"},
        )

        data = entry.model_dump()

        assert data["action_id"] == "ACT003"
        assert data["actor"]["os_user"] == "testuser"
        assert data["actor"]["display_name"] == "Test User"
        assert data["target"]["entity_type"] == "qa"
        assert data["target"]["entity_id"] == "QA001"
        assert data["outcome"] == "success"
        assert data["context"]["validator"] == "human"


class TestModelsExport:
    """Test that models are properly exported from models package."""

    def test_actor_identity_exported_from_models_package(self) -> None:
        """ActorIdentity should be importable from models package."""
        from models import ActorIdentity

        actor = ActorIdentity(os_user="test", display_name=None)
        assert actor.os_user == "test"

    def test_get_current_actor_exported_from_models_package(self) -> None:
        """get_current_actor should be importable from models package."""
        from models import get_current_actor

        actor = get_current_actor()
        assert actor.os_user is not None

    def test_audit_entry_exported_from_models_package(self) -> None:
        """AuditEntry should be importable from models package."""
        from models import AuditEntry, AuditTarget, ActorIdentity

        actor = ActorIdentity(os_user="test", display_name=None)
        target = AuditTarget(entity_type="task", entity_id="T001")
        timestamp = datetime.now(timezone.utc)

        entry = AuditEntry(
            action_id="ACT001",
            actor=actor,
            timestamp=timestamp,
            action_type="test",
            target=target,
            outcome="success",
            context=None,
        )
        assert entry.action_id == "ACT001"

    def test_audit_target_exported_from_models_package(self) -> None:
        """AuditTarget should be importable from models package."""
        from models import AuditTarget

        target = AuditTarget(entity_type="task", entity_id="T001")
        assert target.entity_type == "task"
