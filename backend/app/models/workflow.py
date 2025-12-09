from datetime import UTC, datetime
from enum import Enum
from typing import Any

from beanie import Document, Indexed
from pydantic import Field


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class ThreadStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Workflow(Document):
    """Workflow document storing workflow definitions."""

    name: Indexed(str)  # type: ignore[valid-type]
    description: str = ""
    status: WorkflowStatus = WorkflowStatus.DRAFT
    graph_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "workflows"
        indexes = [
            "status",
            "created_at",
        ]


class Thread(Document):
    """Thread document storing LangGraph execution threads."""

    workflow_id: Indexed(str)  # type: ignore[valid-type]
    status: ThreadStatus = ThreadStatus.PENDING
    current_node: str | None = None
    input_data: dict[str, Any] = Field(default_factory=dict)
    output_data: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "threads"
        indexes = [
            "workflow_id",
            "status",
            "created_at",
        ]
