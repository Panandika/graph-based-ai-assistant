from datetime import UTC, datetime
from enum import Enum
from typing import Any

from beanie import Document, Indexed
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    LLM = "llm"
    TOOL = "tool"
    CONDITION = "condition"
    START = "start"
    END = "end"


class Position(BaseModel):
    """Node position in the graph UI."""

    x: float = 0.0
    y: float = 0.0


class NodeData(BaseModel):
    """Data associated with a graph node."""

    label: str
    node_type: NodeType
    config: dict[str, Any] = Field(default_factory=dict)


class GraphNode(BaseModel):
    """A node in the graph."""

    id: str
    type: str = "custom"
    position: Position
    data: NodeData


class GraphEdge(BaseModel):
    """An edge connecting two nodes."""

    id: str
    source: str
    target: str
    source_handle: str | None = None
    target_handle: str | None = None
    label: str | None = None
    condition: str | None = None


class Graph(Document):
    """Graph document storing node/edge configurations for React Flow."""

    name: Indexed(str)  # type: ignore[valid-type]
    description: str = ""
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "graphs"
        indexes = [
            "created_at",
        ]
