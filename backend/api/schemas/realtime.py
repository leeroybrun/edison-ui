"""Realtime WebSocket message schemas (T050).

Defines Pydantic schemas for WebSocket protocol messages per data-model.md:
- SubscribeMessage: Client subscribes to a resource
- UnsubscribeMessage: Client unsubscribes from a resource
- SnapshotMessage: Server sends full dataset snapshot
- UpsertMessage: Server sends entity created/updated
- DeleteMessage: Server sends entity deleted
- ErrorMessage: Server sends error response
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SubscribeMessage(BaseModel):
    """Client message to subscribe to a resource."""

    type: str = "subscribe"
    subscription_id: str = Field(..., alias="subscriptionId")
    resource: str
    params: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class UnsubscribeMessage(BaseModel):
    """Client message to unsubscribe from a resource."""

    type: str = "unsubscribe"
    subscription_id: str = Field(..., alias="subscriptionId")

    model_config = {"populate_by_name": True}


class SnapshotMessage(BaseModel):
    """Server message containing full dataset snapshot."""

    type: str = "snapshot"
    subscription_id: str = Field(..., alias="subscriptionId")
    revision: int
    data: list[dict[str, Any]]

    model_config = {"populate_by_name": True}


class UpsertMessage(BaseModel):
    """Server message for entity create/update."""

    type: str = "upsert"
    subscription_id: str = Field(..., alias="subscriptionId")
    revision: int
    data: dict[str, Any]

    model_config = {"populate_by_name": True}


class DeleteMessage(BaseModel):
    """Server message for entity deletion."""

    type: str = "delete"
    subscription_id: str = Field(..., alias="subscriptionId")
    revision: int
    id: str

    model_config = {"populate_by_name": True}


class ErrorMessage(BaseModel):
    """Server message for errors."""

    type: str = "error"
    subscription_id: str | None = Field(None, alias="subscriptionId")
    code: str
    message: str

    model_config = {"populate_by_name": True}
