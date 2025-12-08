from datetime import datetime

from pydantic import BaseModel, Field

from app.models.graph import GraphEdge, GraphNode


class GraphCreate(BaseModel):
    """Schema for creating a graph."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


class GraphUpdate(BaseModel):
    """Schema for updating a graph."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    nodes: list[GraphNode] | None = None
    edges: list[GraphEdge] | None = None


class GraphResponse(BaseModel):
    """Schema for graph response."""

    id: str
    name: str
    description: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    created_at: datetime
    updated_at: datetime
