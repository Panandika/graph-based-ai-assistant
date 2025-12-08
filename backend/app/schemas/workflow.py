from datetime import datetime

from pydantic import BaseModel, Field

from app.models.workflow import ThreadStatus, WorkflowStatus


class WorkflowCreate(BaseModel):
    """Schema for creating a workflow."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    graph_id: str | None = None


class WorkflowUpdate(BaseModel):
    """Schema for updating a workflow."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: WorkflowStatus | None = None
    graph_id: str | None = None


class WorkflowResponse(BaseModel):
    """Schema for workflow response."""

    id: str
    name: str
    description: str
    status: WorkflowStatus
    graph_id: str | None
    created_at: datetime
    updated_at: datetime


class ThreadCreate(BaseModel):
    """Schema for creating a thread execution."""

    input_data: dict = Field(default_factory=dict)


class ThreadResponse(BaseModel):
    """Schema for thread response."""

    id: str
    workflow_id: str
    status: ThreadStatus
    current_node: str | None
    input_data: dict
    output_data: dict
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class ExecuteWorkflowRequest(BaseModel):
    """Schema for executing a workflow."""

    input_data: dict = Field(default_factory=dict)


class ExecuteWorkflowResponse(BaseModel):
    """Schema for workflow execution response."""

    thread_id: str
    status: ThreadStatus
